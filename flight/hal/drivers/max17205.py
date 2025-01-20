# Fuel Gauge IC MAX17205 driver
import time, math
from adafruit_bus_device.i2c_device import I2CDevice
from micropython import const


MAX1720X_I2CADDR_WR = 0x0B
MAX1720X_I2CADDR_RD = 0x36

MAX1720X_STATUS_ADDR = 0x00  # Contains alert status and chip status
MAX1720X_VCELL_ADDR = 0x09  # Lowest cell voltage of a pack
MAX1720X_REPSOC_ADDR = 0x06  # Reported state of charge
MAX1720X_REPCAP_ADDR = 0x05  # Reported remaining capacity
MAX1720X_TEMP_ADDR = 0x08  # Temperature
MAX1720X_CURRENT_ADDR = 0x0A  # Battery current
MAX1720X_TTE_ADDR = 0x11  # Time to empty
MAX1720X_TTF_ADDR = 0x20  # Time to full
MAX1720X_CAPACITY_ADDR = 0x10  # Full capacity estimation
MAX1720X_VBAT_ADDR = 0xDA  # Battery pack voltage
MAX1720X_AVCELL_ADDR = 0x17  # Battery cycles
MAX1720X_TIMERH_ADDR = 0xBE  # Time since power up

MAX1720X_COMMAND_ADDR = 0x60  # Command register
MAX1720X_CONFIG2_ADDR = 0xBB  # Command register
MAX1720X_CFGPACK_ADDR = 0xB5  # nPackCfg register

NPACKCFG_BALCFG = const(0x7 << 5) # cell balance config 


def unpack_signed_short_int(byte_list):
    """
    Unpacks a signed 2-byte integer from a list of 2 bytes.

    :param byte_list: List of 2 bytes representing the packed 2-byte signed
    integer.
    :return: Unpacked signed 2-byte integer.
    """
    val = (byte_list[1] << 8) | byte_list[0]
    return val if val < 0x8000 else val - 0x10000


class MAX17205():
    def __init__(self, i2c):
        self.i2c_device = I2CDevice(i2c, MAX1720X_I2CADDR_RD)
        self.i2c_device_cfg = I2CDevice(i2c, MAX1720X_I2CADDR_WR)
        self.rx_buffer = bytearray(2)

        self.voltage = 0.0
        self.current = 0.0
        self.midvoltage = 0.0

        self.soc = 0
        self.capacity = 0
        self.cycles = 0
        self.tte = 0
        self.ttf = 0
        self.time_pwrup = 0

        # with self.i2c_device_cfg as i2c:
        #     # Read 2 bytes from MAX1720X_CFGPACK_ADDR
        #     i2c.write(bytes([MAX1720X_CFGPACK_ADDR, DATA_LOW, DATA_HIGH]))
    def enable_cell_balancing(self, threshold):
        balcfg = int(math.log2(threshold / (0.00125))) # need to adjust this
        with self.i2c_device_cfg as i2c:
            i2c.write(bytes([MAX1720X_CFGPACK_ADDR, balcfg]))

    def read_cfg(self):
        with self.i2c_device_cfg as i2c:
            # Read 2 bytes from MAX1720X_CFGPACK_ADDR
            i2c.write(bytes([MAX1720X_CFGPACK_ADDR]))

        with self.i2c_device_cfg as i2c:
            i2c.readinto(self.rx_buffer)

        return self.rx_buffer

    def read_soc(self):
        """
        Reads SoC from the battery pack.

        :return: SoC as a percentage.
        """
        with self.i2c_device as i2c:
            # Read 2 bytes from MAX1720X_REPSOC_ADDR
            i2c.write(bytes([MAX1720X_REPSOC_ADDR]))
            i2c.readinto(self.rx_buffer)

        # Convert readback bytes to pack SoC
        self.soc = int.from_bytes(
            self.rx_buffer, 'little', signed=False) / 256

        return self.soc

    def read_capacity(self):
        """
        Reads capacity from the battery pack.

        :return: Capacity in mAh.
        """
        with self.i2c_device as i2c:
            # Read 2 bytes from MAX1720X_REPCAP_ADDR
            i2c.write(bytes([MAX1720X_REPCAP_ADDR]))
            i2c.readinto(self.rx_buffer)

        # Convert readback bytes to pack capacity
        self.capacity = int.from_bytes(
            self.rx_buffer, 'little', signed=False) / 0.01

        return self.capacity

    def read_current(self):
        """
        Reads the current from the battery pack.

        :return: Current in mA as a float.
        """
        with self.i2c_device as i2c:
            # Read 2 bytes from MAX1720X_CURRENT_ADDR
            i2c.write(bytes([MAX1720X_CURRENT_ADDR]))
            i2c.readinto(self.rx_buffer)

        # Convert readback bytes to an int16
        current_raw = unpack_signed_short_int(self.rx_buffer)

        # Cast int16 to a float and scale for mA current
        self.current = float(current_raw) * 0.0015625/0.01

        return self.current

    def read_voltage(self):
        """
        Reads the voltage for the battery pack.

        :return: Voltage in mV as a float.
        """
        with self.i2c_device as i2c:
            # Read 2 bytes from MAX1720X_VBAT_ADDR
            i2c.write(bytes([MAX1720X_VBAT_ADDR]))
            i2c.readinto(self.rx_buffer)

        # Convert readback bytes to a uint16
        voltage_raw = int.from_bytes(self.rx_buffer, 'little', signed=False)

        # Cast uint16 to a float and scale for mV voltage
        self.voltage = float(voltage_raw) * 1.25

        return self.voltage

    def read_midvoltage(self):
        """
        Reads the midpoint voltage for the battery pack.

        :return: Voltage in mV as a float.
        """
        with self.i2c_device as i2c:
            # Read 2 bytes from MAX1720X_VCELL_ADDR
            i2c.write(bytes([MAX1720X_VCELL_ADDR]))
            i2c.readinto(self.rx_buffer)

        # Convert readback bytes to a uint16
        midvoltage_raw = int.from_bytes(self.rx_buffer, 'little', signed=False)

        # Cast uint16 to a float and scale for mV voltage
        self.midvoltage = float(midvoltage_raw) * 0.078125

        return self.midvoltage

    def read_cycles(self):
        """
        Reads the battery cycles for the battery pack.

        :return: Number of cycles.
        """
        with self.i2c_device as i2c:
            # Read 2 bytes from MAX1720X_AVCELL_ADDR
            i2c.write(bytes([MAX1720X_AVCELL_ADDR]))
            i2c.readinto(self.rx_buffer)

        # Convert readback bytes to a uint16
        self.cycles = int.from_bytes(
            self.rx_buffer, 'little', signed=False)

        return self.cycles

    def read_tte(self):
        """
        Reads the time-to-empty for the battery pack.

        :return: Time-to-empty in seconds
        """
        with self.i2c_device as i2c:
            # Read 2 bytes from MAX1720X_TTE_ADDR
            i2c.write(bytes([MAX1720X_TTE_ADDR]))
            i2c.readinto(self.rx_buffer)

        # Convert readback bytes to a uint16
        self.tte = int.from_bytes(
            self.rx_buffer, 'little', signed=False) * 5.625

        return self.tte

    def read_ttf(self):
        """
        Reads the time-to-full for the battery pack.

        :return: Time-to-full in seconds
        """
        with self.i2c_device as i2c:
            # Read 2 bytes from MAX1720X_TTF_ADDR
            i2c.write(bytes([MAX1720X_TTF_ADDR]))
            i2c.readinto(self.rx_buffer)

        # Convert readback bytes to a uint16
        self.ttf = int.from_bytes(
            self.rx_buffer, 'little', signed=False) * 5.625

        return self.ttf

    def read_time_pwrup(self):
        """
        Reads the time since power up for the battery pack.

        :return: Time since power up in seconds
        """
        with self.i2c_device as i2c:
            # Read 2 bytes from MAX1720X_TIMERH_ADDR
            i2c.write(bytes([MAX1720X_TIMERH_ADDR]))
            i2c.readinto(self.rx_buffer)

        # Convert readback bytes to a uint16
        self.time_pwrup = int.from_bytes(
            self.rx_buffer, 'little', signed=False)

        return self.time_pwrup

    def reset(self):
        """
        Resets the fuel gauge IC.

        :return: None
        """
        # with self.i2c_device as i2c:
        #     # Write to MAX1720X_COMMAND_ADDR
        #     i2c.write(bytes([MAX1720X_COMMAND_ADDR, 0x0F, 0x00]))

        # # Wait
        # time.sleep(50/1000)

        with self.i2c_device as i2c:
            # Write to MAX1720X_CONFIG2_ADDR
            i2c.write(bytes([MAX1720X_CONFIG2_ADDR, 0x01, 0x00]))