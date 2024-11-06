import time

from hal.drivers.middleware.errors import Errors
from hal.drivers.middleware.generic_driver import Driver


class CubeSat:
    """CubeSat: Base class for all CubeSat implementations"""

    __slots__ = (
        "__device_list",
        "__recent_errors",
        "__state_flags",
        "__uart1",
        "__uart2",
        "__spi",
        "__i2c1",
        "__i2c2",
        "__gps",
        "__battery_monitor",
        "__jetson_monitor",
        "__imu",
        "__charger",
        "__torque_x",
        "__torque_y",
        "__torque_z",
        "__light_sensors",
        "__rtc",
        "__radio",
        "__sd_card",
        "__burn_wires",
        "__vfs",
        "__payload_uart",
        "_time_ref_boot",
    )

    def __init__(self):
        # List of successfully initialized devices
        self.__device_list: list[Driver] = []

        # List of errors from most recent system diagnostic test
        self.__recent_errors: list[int] = [Errors.NOERROR]

        # State flags
        self.__state_flags = None

        # # # Interfaces
        # self.__uart1 = None
        # self.__uart2 = None
        # self.__spi = None
        # self.__i2c1 = None
        # self.__i2c2 = None

        # Devices
        self.__charger = None
        self.__imu = None
        self.__light_sensors = {}
        self.__torque_drivers = {}
        self.__power_monitors = {}
        self.__fuel_gauge = None
        self.__rtc = None
        self.__gps = None
        self.__radio = None
        self.__sd_card = None
        self.__burn_wires = None
        self.__payload_spi = None
        self.__vfs = None

        # Debugging
        self._time_ref_boot = int(time.time())

    # ABSTRACT METHOD #
    def boot_sequence(self) -> list[int]:
        """boot_sequence: Boot sequence for the CubeSat."""
        raise NotImplementedError("CubeSats must implement boot method")

    # ABSTRACT METHOD #
    def run_system_diagnostics(self) -> list[int] | None:
        """run_diagnostic_test: Run all tests for the component"""
        raise NotImplementedError("CubeSats must implement diagnostics method")

    def get_recent_errors(self) -> list[int]:
        """get_recent_errors: Get the most recent errors from the system"""
        return self._recent_errors

    @property
    def device_list(self):
        """device_list: Get the list of successfully initialized devices"""
        return self.__device_list

    def append_device(self, device):
        """append_device: Append a device to the device list"""
        self.__device_list.append(device)

    ######################### STATE FLAGS ########################
    @property
    def STATE_FLAGS(self):
        """STATE_FLAGS: Returns the state flags object
        :return: object or None
        """
        return self._state_flags

    # ######################### INTERFACES #########################

    # @property
    # def UART1(self):
    #     """UART: Returns the UART interface"""
    #     return self.__uart1

    # @property
    # def UART2(self):
    #     """UART2: Returns the UART2 interface"""
    #     return self.__uart2

    # @property
    # def SPI(self):
    #     """SPI: Returns the SPI interface"""
    #     return self.__spi

    # @property
    # def I2C1(self):
    #     """I2C: Returns the I2C interface"""
    #     return self.__i2c1

    # @property
    # def I2C2(self):
    #     """I2C2: Returns the I2C2 interface"""
    #     return self.__i2c2

    ######################### DEVICES #########################

    @property
    def GPS(self):
        """GPS: Returns the gps object
        :return: object or None
        """
        return self.__gps

    @property
    def POWER_MONITORS(self):
        """POWER_MONITORS: Returns a dictionary of power monitor with their locations
        :return: object or None
        """
        return self.__power_monitors

    @property
    def IMU(self):
        """IMU: Returns the IMU object
        :return: object or None
        """
        return self.__imu

    @property
    def CHARGER(self):
        """CHARGER: Returns the charger object
        :return: object or None
        """
        return self.__charger

    @property
    def TORQUE_DRIVERS(self):
        """Returns a dictionary of torque drivers with the direction as the key (e.g. 'XP', 'XM', 'YP', 'YM', 'ZM')"""
        return self.__torque_drivers

    @property
    def FUEL_GAUGE(self):
        """FUEL_GAUGE: Returns the fuel gauge object
        :return: object or None
        """
        return self.__fuel_gauge

    # ABSTRACT METHOD #
    def APPLY_MAGNETIC_CONTROL(self) -> None:
        """CONTROL_COILS: Control the coils on the CubeSat, depending on the control mode (identiical for all coils)."""
        raise NotImplementedError("CubeSats must implement the control coils method")

    @property
    def LIGHT_SENSORS(self):
        """Returns a dictionary of light sensors with the direction as the key (e.g. 'XP', 'XM', 'YP', 'YM', 'ZM')"""
        return self.__light_sensors

    @property
    def RTC(self):
        """RTC: Returns the RTC object
        :return: object or None
        """
        return self.__rtc

    @property
    def RADIO(self):
        """RADIO: Returns the radio object
        :return: object or None
        """
        return self.__radio

    @property
    def BURN_WIRES(self):
        """BURN_WIRES: Returns the burn wire object
        :return: object or None
        """
        return self.__burn_wires

    @property
    def SD_CARD(self):
        """SD_CARD: Returns the SD card object
        :return: object or None
        """
        return self.__sd_card

    @property
    def VFS(self):
        """VFS: Returns the VFS object
        :return: object or None
        """
        return self.__vfs

    @property
    def PAYLOADUART(self):
        """PAYLOAD_EN: Returns the payload enable object
        :return: object or None
        """
        return self.__payload_uart

    @property
    def BOOTTIME(self):
        """BOOTTIME: Returns the reference count since the board booted
        :return: object or None
        """
        return self._time_ref_boot
