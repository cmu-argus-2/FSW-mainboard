"""
CircuitPython driver for the OPT4003 ALS

**Authors**
Thomas Damiani
Neil Khera

**Sofware Requirements**

* Adafruit CircuitPython Firmware (8.0.5+)
    https://github.com/adafruit/circuitpython/releases/tag/8.0.5
* Adafruit Bus Device Library
    https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit Register Library
    https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

import time

from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_register.i2c_bit import ROBit, RWBit
from adafruit_register.i2c_bits import RWBits

# from micropython import const


try:
    from busio import I2C
except ImportError:
    pass

# Registers as descirbed in page 25 of datasheet
_RESULT_MSB_CH0 = 0x00
_RESULT_LSB_CH0 = 0x01
# _RESULT_MSB_CH1 = 0x02
# RESULT_LSB_CH1 = 0x03
# FIFO_MSB_CH0 = 0x04
# FIFO_LSB_CH0 = 0x05
# FIFO_MSB_CH1 = 0x06
# FIFO_LSB_CH1 = 0x07
# THRESHOLD_L = 0x08
# THRESHOLD_H = 0x09
_CONFIGURATION = 0x0A
_FLAGS = 0x0C
_DEVICE_ID = 0x11


class OPT4003:
    """
    Driver for the OPT4003 ambient light sensor

    Positional Arguments
    ++++++++++++++++++++

    **i2c_bus**

    Type - busio.I2C.\n
    The i2c_bus you are using for I2C communication.

    **address**

    The i2c address of the sun sensor you are using. the default is 0x44

    Keyword Arguments
    +++++++++++++++++

    * bold value is the default value

    **quick_wakeup**

    wakeup mode from Standby in one-shot mode. True activates quick Wake-up which
    gets out of standby faster as the cost of larger power consumption.

    +-------------------------------+-----------------------+
    | True                          | **False**             |
    +-------------------------------+-----------------------+
    | active                        | **inactive**          |
    +-------------------------------+-----------------------+


    **lux_range**

    the range which the result register will use to return a result

    +-----------+-----------+-----------+-----------+-----------+
    | 0         | 1         | 2         | 3         | 4         |
    +-----------+-----------+-----------+-----------+-----------+
    | 561 lux   | 1122 lux  | 2.2 klux  | 4.4 klux  | 8.9 klux  |
    +-----------+-----------+-----------+-----------+-----------+
    +-----------+-----------+-----------+-----------+-----------+
    | 5         | 6         | 7         | 8         | **12**    |
    +-----------+-----------+-----------+-----------+-----------+
    | 17.9 klux | 35.9 klux | 71.8 klux | 143.6 klux| **auto**  |
    +-----------+-----------+-----------+-----------+-----------+

    **conversion_time**

    How long the device will take to be ready with the next measurement

    +-----------+-----------+-----------+-----------+-----------+-----------+
    | 0         | 1         | 2         | 3         | 4         | 5         |
    +-----------+-----------+-----------+-----------+-----------+-----------+
    | 600us     | 1ms       | 1.8ms     | 3.4ms     | 6.5ms     | 12.7ms    |
    +-----------+-----------+-----------+-----------+-----------+-----------+
    +-----------+-----------+-----------+-----------+-----------+-----------+
    | 6         | 7         | **8**     | 9         | 10        | 11        |
    +-----------+-----------+-----------+-----------+-----------+-----------+
    | 25ms      | 50ms      | **100ms** | 200ms     | 400ms     | 800ms     |
    +-----------+-----------+-----------+-----------+-----------+-----------+

    **Operating Mode**

    what mode the sensor will operate in

    +-----------+-----------+-----------+-----------+
    | **0**     | 1         | 2         | 3         |
    +-----------+-----------+-----------+-----------+
    | **Power   | Forced    | One-shot  | continuous|
    | Down**    | auto-range|           |           |
    |           | One-shot  |           |           |
    +-----------+-----------+-----------+-----------+

    **Latch**

    which interrupt mechanism the sensor will use when an interrupt is needed. Interrupt
    reporting mechanisms as described in page 14 and 15 of the datasheet\n

    +-------------------------------+-----------------------+
    | True                          | **False**             |
    +-------------------------------+-----------------------+
    | Transparent hysteresis mode   |**Latched window mode**|
    +-------------------------------+-----------------------+

    **int_pol**

    INT pin polarity

    +-------------------------------+-----------------------+
    | True                          | **False**             |
    +-------------------------------+-----------------------+
    | Active High                   | **Active Low**        |
    +-------------------------------+-----------------------+

    **fault_count**

    describes how many consecutive faults are required to trigger the theshold mechanisms.\n
    +------------+-----------+-----------+-----------+-----------+
    |input       | **0**     | 1         | 2         | 3         |
    +------------+-----------+-----------+-----------+-----------+
    |fault count | **one**   | two       | four      | eight     |
    +------------+-----------+-----------+-----------+-----------+

    """

    # Configuration settings
    # Locations of these bits are descirbed in page 30 and 31 of the datasheet
    quick_wakeup = RWBit(_CONFIGURATION, 15, register_width=2, lsb_first=False)
    lux_range = RWBits(4, _CONFIGURATION, 10, register_width=2, lsb_first=False)
    conversion_time = RWBits(4, _CONFIGURATION, 6, register_width=2, lsb_first=False)
    operating_mode = RWBits(2, _CONFIGURATION, 4, register_width=2, lsb_first=False)
    latch = RWBit(_CONFIGURATION, 3, register_width=2, lsb_first=False)
    int_pol = RWBit(_CONFIGURATION, 2, register_width=2, lsb_first=False)
    fault_count = RWBits(2, _CONFIGURATION, 0, register_width=2, lsb_first=False)

    # flags
    overload_flag = ROBit(_FLAGS, 3, register_width=2, lsb_first=False)
    conversion_ready_flag = ROBit(_FLAGS, 2, register_width=2, lsb_first=False)
    flag_h = ROBit(_FLAGS, 1, register_width=2, lsb_first=False)
    flag_L = ROBit(_FLAGS, 0, register_width=2, lsb_first=False)

    def __init__(
        self,
        i2c_bus: I2C,
        address: int = 0x44,
        quick_wakeup: bool = False,
        lux_range: int = 0b1100,
        conversion_time: int = 0b1000,
        operating_mode: int = 0b11,
        latch: bool = True,
        int_pol: bool = False,
        fault_count: int = 0b00,
    ) -> "OPT4003":

        self.i2c_device = I2CDevice(i2c_bus, address)
        """
        i2c_device: and I2CDevice initialized using the input i2c_bus and address
        """

        self.quick_wakeup = quick_wakeup
        """
        quick_wakeup: wakeup mode from Standby in one-shot mode. True activates quick Wake-up which
        gets out of standby faster as the cost of larger power consumption.

        """

        self.lux_range = lux_range
        """
        Lux range: the range which the result will use to return a result\n
        | 0         | 1         | 2         | 3         | 4         | 5         |
        | 561 lux   | 1122 lux  | 2.2 klux  | 4.4 klux  | 8.9 klux  | 17.9 klux |

        | 6         | 7         | 8         | 12        |
        | 35.9 klux | 71.8 klux | 143.6 klux| auto      |
        """

        self.conversion_time = conversion_time
        """
        Conversion Time: How long the device will take to be ready with the next measurement\n
        | 0         | 1         | 2         | 3         | 4         | 5         |
        | 600us     | 1ms       | 1.8ms     | 3.4ms     | 6.5ms     | 12.7ms    |

        | 6         | 7         | 8         | 9         | 10        | 11        |
        | 25ms      | 50ms      | 100ms     | 200ms     | 400ms     | 800ms     |
        """

        self.operating_mode = operating_mode
        """
        Operating Mode\n
        0: Power Down\n
        1: Forced Auto-range One-shot\n
        2: One-shot\n
        3: Continuous\n
        """

        self.latch = latch
        """
        Interrupt reporting mechanisms as described in page 14 and 15 of the datasheet\n
        0: Transparent hysteresis mode\n
        1: Latched window mode\n
        """

        self.int_pol = int_pol
        """
        INT pin polarity\n
        0: Active Low\n
        1: Active High\n
        """

        self.fault_count = fault_count
        """
        Fault count describes how many consecutive faults are required to trigger the theshold
        mechanisms.\n
        0: one fault\n
        1: two faults\n
        2: four faults\n
        3: eight faults\n
        """

        self.buf = bytearray(3)

        # check that the ID of the device matches what the datasheet says the ID should be
        if not self.check_id():
            raise RuntimeError("Could not read device id")

    def read_u16(self, addr) -> None:
        # first write will be to the address register
        self.buf[0] = addr
        with self.i2c_device as i2c:
            # write to the address register, then read from register into buffer[0] and buffer[1]
            i2c.write_then_readinto(self.buf, self.buf, out_end=1, in_start=0)

    def check_id(self) -> bool:
        # first check that DIDL == 0
        self.read_u16(_DEVICE_ID)
        DIDL = (self.buf[0] >> 4) & ((1 << 2) - 1)  # 13-12
        if not DIDL == 0:
            return False

        # second check that DIDH == 0x121
        DIDH = self.buf[0] & ((1 << 4) - 1)  # 11-8
        DIDH = (DIDH << 8) + self.buf[1]  # add 7-0
        if not (DIDH == 0x221):
            return False

        return True

    def get_exp_msb(self, register) -> tuple:
        # read register into buffer
        self.read_u16(register)

        # separate each component
        exponent = (self.buf[0] >> 4) & ((1 << 4) - 1)  # 15-12

        result_msb = self.buf[0] & ((1 << 4) - 1)  # 11-8
        result_msb = result_msb << 8  # pad
        result_msb += self.buf[1]  # add 7-0

        return exponent, result_msb

    def get_lsb_counter_crc(self, register) -> tuple:
        # read register into buffer
        self.read_u16(register)

        # separate each component
        result_lsb = self.buf[0]  # 15-8
        counter = (self.buf[1] >> 4) & ((1 << 4) - 1)  # 7-4
        crc = self.buf[1] & ((1 << 4) - 1)  # 3-0

        return result_lsb, counter, crc

    def result_of_addr(self, just_lux) -> list:
        """
        Gets Lux value from the result register. returns lux value as a float.
        If just_lux is false the counter and crc bits will be added and a tuple of the
        3 measurements will be returned
        """

        # wait for conversion to be ready
        start_time = time.monotonic() + 1.1
        while time.monotonic() < start_time:
            if self.conversion_ready_flag:
                # return -1
                break
            time.sleep(0.001)

        """
        15-12: EXPONENT
        11-0: RESULT_MSB
        """
        exponent, result_msb = self.get_exp_msb(_RESULT_MSB_CH0)

        """
        15-8: RESULT_LSB
        7-4: COUNTER
        3-0: CRC

        Calculation for the CRC bits are as follows
        E = exponent
        R = result
        C = counter
        X[0]=XOR(E[3:0],R[19:0],C[3:0]) XOR of all bits
        X[1]=XOR(C[1],C[3],R[1],R[3],R[5],R[7],R[9],R[11],R[13],R[15],R[17],R[19],E[1],E[3])
        X[2]=XOR(C[3],R[3],R[7],R[11],R[15],R[19],E[3])
        X[3]=XOR(R[3],R[11],R[19])
        """
        result_lsb, _, _ = self.get_lsb_counter_crc(_RESULT_LSB_CH0)

        # equations from pages 17 and 18 of datasheet
        mantissa = (result_msb << 8) + result_lsb
        adc_codes = mantissa << exponent
        lux = adc_codes * 0.000535

        return lux

    def lux(self) -> float:
        """
        Reads out JUST the lux value from the result register. The lux is calculated from the
        0x00 register and the 8 most significant bits of the 0x01 register.

        From the 0x00 register bits 15-12 are the EXPONENT (E), while bits 11-0 are the RESULT_MSB. From
        the 0x01 register bits 15-8 are the RESULT_LSB.

        lux is calculated via:

        lux = (((RESULT_MSB << 8) + RESULT_LSB) << EXPONENT) * 535E-6
        """
        return self.result_of_addr(False)

    @property
    def result(self) -> tuple:
        """
        Returns, as a tuple, the lux calculated from the register, the counter, and the crc bits

        The Lux is calculated in the same way as the lux property. Refer to the lux property function for
        a detailed description of the calculation.

        The counter will count from 0 to 15 and then restart at 0 again. It is for knowing you have
        successive measurements.

        The CRC bits are for ensuring you are recieving the proper bits over your channel. The calcuation
        for these bits is as follows:
        E = exponent bits
        R = result bits
        C = counter bits

        X[0]
            XOR ( E[3:0],R[19:0],C[3:0]) XOR of all bits
        X[1]
            XOR ( C[1], C[3], R[1], R[3], R[5], R[7], R[9], R[11], R[13], R[15], R[17], R[19], E[1], E[3])
        X[2]
            XOR ( C[3], R[3], R[7], R[11], R[15], R[19], E[3])
        X[3]
            XOR ( R[3], R[11], R[19])
        """
        return self.result_of_addr(False)

    def deinit(self):
        return