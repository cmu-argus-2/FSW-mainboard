"""
`adm1176`
====================================================

CircuitPython driver for the adm1176 hot swap controller and I2C power monitor

* Author(s): Max Holliday, Harry Rosmann

Implementation Notes
--------------------

"""

from adafruit_bus_device.i2c_device import I2CDevice
from hal.drivers.errors import Errors
from micropython import const

# def _to_signed(num):
#     if num > 0x7FFF:
#         num -= 0x10000
#     return num


_DATA_V_MASK = const(0xF0)
_DATA_I_MASK = const(0x0F)
_cmd = bytearray(1)
_extcmd = bytearray(b"\x00\x04")
_BUFFER = bytearray(3)
_STATUS = bytearray(1)

# Status register
_STATUS_READ = const(0x1 << 6)
# _STATUS_ADC_OC = const(0x1 << 0)
_STATUS_ADC_ALERT = const(0x1 << 1)
# _STATUS_HS_OC = const(0x1 << 2)
# STATUS_HS_ALERT = const(0x1 << 3)
_STATUS_OFF_STATUS = const(0x1 << 4)
# STATUS_OFF_ALERT = const(0x1 << 5)

# Extended registers
_ALERT_EN_EXT_REG_ADDR = const(0x81)
_ALERT_EN_EN_ADC_OC4 = const(0x1 << 1)
_ALERT_EN_CLEAR = const(0x1 << 4)

_ALERT_TH_EN_REG_ADDR = const(0x82)

_CONTROL_REG_ADDR = const(0x83)
_CONTROL_SWOFF = const(0x1 << 0)


class ADM1176:
    # def __init__(self, i2c_bus, addr=0x4A):
    def __init__(self, i2c_bus, addr):
        self.i2c_device = I2CDevice(i2c_bus, addr, probe=False)
        self.i2c_addr = addr
        self.sense_resistor = 0.01
        self.config("V_CONT,I_CONT")

        self._on = True
        self._overcurrent_level = 0xFF

        # Voltage conversions
        # VI_RESOLUTION = const(4096)
        # I_FULLSCALE = 0.10584
        # V_FULLSCALE = 26.35

        self.v_fs_over_res = 26.35 / 4096
        self.i_fs_over_res = 0.10584 / 4096

    def reset(self) -> None:
        """reset: Resets the device and clears all registers.

        :return: None
        """
        pass

    def config(self, value: str) -> None:
        """config: sets voltage current readout configuration.

        :param value: Current and voltage register values
        based on string.
        """
        V_CONT_BIT = const(0x1 << 0)
        V_ONCE_BIT = const(0x1 << 1)
        I_CONT_BIT = const(0x1 << 2)
        I_ONCE_BIT = const(0x1 << 3)
        V_RANGE_BIT = const(0x1 << 4)

        _cmd[0] = 0x00
        if "V_CONT" in value:
            _cmd[0] |= V_CONT_BIT
        if "V_ONCE" in value:
            _cmd[0] |= V_ONCE_BIT
        if "I_CONT" in value:
            _cmd[0] |= I_CONT_BIT
        if "I_ONCE" in value:
            _cmd[0] |= I_ONCE_BIT
        if "VRANGE" in value:
            _cmd[0] |= V_RANGE_BIT
        with self.i2c_device as i2c:
            i2c.write(_cmd)

    def read_voltage_current(self) -> tuple[float, float]:
        """read_voltage current: gets the current voltage and current
        (V, I) pair.

        :return: instantaneous (V,I) pair
        """

        with self.i2c_device as i2c:
            i2c.readinto(_BUFFER)
        raw_voltage = ((_BUFFER[0] << 8) | (_BUFFER[2] & _DATA_V_MASK)) >> 4
        raw_current = (_BUFFER[1] << 4) | (_BUFFER[2] & _DATA_I_MASK)
        _voltage = (self.v_fs_over_res) * raw_voltage  # volts
        _current = ((self.i_fs_over_res) * raw_current) / self.sense_resistor  # amperes
        return (_voltage, _current)

    def __turn_off(self) -> None:
        """OFF: Hot-swaps the device out."""
        _extcmd[0] = _CONTROL_REG_ADDR
        _extcmd[1] |= _CONTROL_SWOFF
        with self.i2c_device as i2c:
            i2c.write(_extcmd)

    def __turn_on(self) -> None:
        """ON: Turns the power management IC on, allows it to be
        hot-swapped in, without interrupting power supply.
        """
        _extcmd[0] = _CONTROL_REG_ADDR
        _extcmd[1] &= ~_CONTROL_SWOFF
        with self.i2c_device as i2c:
            i2c.write(_extcmd)
        self.config("V_CONT,I_CONT")

    # def device_on(self) -> bool:
    #     return self._on

    def set_device_on(self, turn_on: bool) -> None:
        if turn_on:
            self.__turn_on()
        else:
            self.__turn_off()

    def device_on(self) -> bool:
        return (self.status() & _STATUS_OFF_STATUS) != _STATUS_OFF_STATUS

    def overcurrent_level(self) -> int:
        """overcurrent_level: Sets the overcurrent level

        :param value: The overcurrent threshold
        # TODO Place relevant conversion equation here
        """
        return self._overcurrent_level

    def set_overcurrent_level(self, value: int = 0xFF) -> None:
        # enable over current alert
        _extcmd[0] = _ALERT_EN_EXT_REG_ADDR
        _extcmd[1] |= _ALERT_EN_EN_ADC_OC4

        with self.i2c_device as i2c:
            i2c.write(_extcmd)
        # set over current threshold
        _extcmd[0] = _ALERT_TH_EN_REG_ADDR
        # set current threshold to value. def=FF which is ADC full scale
        _extcmd[1] = value
        with self.i2c_device as i2c:
            i2c.write(_extcmd)

        self._overcurrent_level = value

    def clear(self) -> None:
        """clear: Clears the alerts after status register read"""
        _extcmd[0] = _ALERT_EN_EXT_REG_ADDR
        temp = _extcmd[1]
        _extcmd[1] |= _ALERT_EN_CLEAR
        with self.i2c_device as i2c:
            i2c.write(_extcmd)
        _extcmd[1] = temp

    def status(self) -> int:
        """status: Returns the status register values

        Bit 0: ADC_OC - Overcurrent detected
        Bit 1: ADC_ALERT - Overcurrent alert
        Bit 2: HS_OC - Hot swap is off because of overcurrent
        Bit 3: HS_ALERT - Hot swap operation failed since last reset
        Bit 4: OFF_STATUS - Status of the ON pin
        Bit 5: OFF_ALERT - An alert has been caused by either the ON pin or the SWOFF bit

        :return: The status bit to be parsed out
        """
        _cmd[0] |= _STATUS_READ  # Read request
        with self.i2c_device as i2c:
            i2c.write(_cmd)
            i2c.readinto(_STATUS)
        _cmd[0] &= ~(_STATUS_READ)
        with self.i2c_device as i2c:
            i2c.write(_cmd)
        return _STATUS[0]

    ######################## ERROR HANDLING ########################

    @property
    def device_errors(self):
        results = []
        status = self.status()
        if status & _STATUS_ADC_ALERT:
            results.append(Errors.PWR_MON_ADC_ALERT_OVERCURRENT)
            self.clear()
        return results

    def deinit(self):
        return
