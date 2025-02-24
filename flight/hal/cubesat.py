import time

from hal.drivers.middleware.errors import Errors

DEVICE = 0
DEVICE_ERROR = 1
DEVICE_BOOT = 2
DEVICE_ARGS = 3


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
        "__power_monitors",
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
        self.__device_list = {
            "SDCARD": [None, 0, self.__sd_card_boot],
            "IMU": [None, 0, self.__imu_boot],
            "RTC": [None, 0, self.__rtc_boot],
            # "GPS": [None, 0, self.__gps_boot],
            # "RADIO": [None, 0, self.__radio_boot],
            "BOARD_PWR": [None, 0, self.__power_monitor_boot],
            # "XP_PWR": [self.__power_monitors["XP"],
            #     self.__power_monitor_boot,
            #     ["XP", ArgusV2Components.XP_POWER_MONITOR_I2C_ADDRESS, ArgusV2Components.XP_POWER_MONITOR_I2C],
            # ],
            # "XM_PWR": [self.__power_monitors["XM"],
            #     self.__power_monitor_boot,
            #     ["XM", ArgusV2Components.XM_POWER_MONITOR_I2C_ADDRESS, ArgusV2Components.XM_POWER_MONITOR_I2C],
            # ],
            # self.__power_monitor["XP"]: self.__power_monitor_boot("XP"),
            # self.__power_monitor["XM"]: self.__power_monitor_boot("XM"),
            # self.__power_monitor["YP"]: self.__power_monitor_boot("YP"),
            # self.__power_monitor["YM"]: self.__power_monitor_boot("YM"),
            # self.__power_monitor["ZP"]: self.__power_monitor_boot("ZP"),
            # self.__power_monitor["ZM"]: self.__power_monitor_boot("ZM"),
        }

        # List of errors from most recent system diagnostic test
        self.__recent_errors: list[int] = [Errors.NOERROR]

        # State flags
        self.__state_flags = None

        # Devices
        # self.__charger = None
        # self.__imu = None
        # self.__light_sensors = {}
        # self.__torque_drivers = {}
        # self.__power_monitors = {
        #     "BOARD": None,
        #     "RADIO": None,
        #     "XP": None,
        #     "XM": None,
        #     "YP": None,
        #     "YM": None,
        #     "ZP": None,
        #     "ZM": None,
        # }
        # self.__fuel_gauge = None
        # self.__rtc = None
        # self.__gps = None
        # self.__radio = None
        # self.__sd_card = None
        # self.__burn_wires = None
        # self.__payload_spi = None
        # self.__vfs = None
        # self.__imu_error = -1
        # self.__charger_error = -1
        # self.__power_monitors_errors = {
        #     "BOARD": -1,
        #     "RADIO": -1,
        #     "XP": -1,
        #     "XM": -1,
        #     "YP": -1,
        #     "YM": -1,
        #     "ZP": -1,
        #     "ZM": -1,
        # }
        # self.__fuel_gauge_error = -1
        # self.__rtc_error = -1
        # self.__gps_error = -1
        # self.__radio_error = -1
        # self.__sd_card_error = -1

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

    @property
    def ERRORS(self):
        """ERRORS: Returns the errors object
        :return: object or None
        """
        error_list = []
        for name, device in self.__device_list.items():
            error_list.append(device[DEVICE_ERROR])
        return error_list

    ######################### STATE FLAGS ########################
    @property
    def STATE_FLAGS(self):
        """STATE_FLAGS: Returns the state flags object
        :return: object or None
        """
        return self._state_flags

    ######################### DEVICES #########################

    @property
    def GPS(self):
        """GPS: Returns the gps object
        :return: object or None
        """
        return self.__device_list["GPS"][DEVICE]

    @property
    def GPS_AVAILABLE(self) -> bool:
        """GPS_AVAILABLE: Returns True if the GPS is available
        :return: bool
        """
        return self.__device_list["GPS"][DEVICE] is not None

    @property
    def POWER_MONITORS(self):
        """POWER_MONITORS: Returns the power monitor object
        :return: object or None
        """
        power_monitors = {"BOARD": self.__device_list["BOARD_PWR"][DEVICE]}
        return power_monitors

    @property
    def BOARD_POWER_MONITOR_AVAILABLE(self) -> bool:
        """BOARD_POWER_MONITOR_AVAILABLE: Returns True if the board power monitor is available
        :return: bool
        """
        return "BOARD" in self.__power_monitors

    @property
    def JETSON_POWER_MONITOR_AVAILABLE(self) -> bool:
        """JETSON_POWER_MONITOR_AVAILABLE: Returns True if the Jetson power monitor is available
        :return: bool
        """
        return "JETSON" in self.__power_monitor

    @property
    def IMU(self):
        """IMU: Returns the IMU object
        :return: object or None
        """
        return self.__device_list["IMU"][DEVICE]

    @property
    def IMU_AVAILABLE(self) -> bool:
        """IMU_AVAILABLE: Returns True if the IMU is available
        :return: bool
        """
        return self.__device_list["IMU"][DEVICE] is not None

    @property
    def IMU_TEMPERATURE_AVAILABLE(self) -> bool:
        """IMU_AVAILABLE: Returns True if the IMU is available
        :return: bool
        """
        return self.__imu_temp_flag

    @property
    def CHARGER(self):
        """CHARGER: Returns the charger object
        :return: object or None
        """
        return self.__charger

    @property
    def CHARGER_AVAILABLE(self) -> bool:
        """CHARGER_AVAILABLE: Returns True if the charger is available
        :return: bool
        """
        return self.__charger is not None

    @property
    def TORQUE_XP_POWER_MONITOR(self):
        """TORQUE_XP: Returns the torque driver in the x+ direction
        :return: object or None
        """
        return self.__torque_xp_power_monitor

    @property
    def TORQUE_XP_POWER_MONITOR_AVAILABLE(self) -> bool:
        """TORQUE_XP_POWER_MONITOR_AVAILABLE: Returns True if the torque driver in the x+ direction is available
        :return: bool
        """
        return self.__torque_xp_power_monitor is not None

    @property
    def TORQUE_DRIVERS(self):
        """Returns a dictionary of torque drivers with the direction as the key (e.g. 'XP', 'XM', 'YP', 'YM', 'ZM')"""
        return self.__torque_drivers

    @property
    def FUEL_GAUGE(self):
        """FUEL_GAUGE: Returns the fuel gauge object
        :return: object or None
        """
        return self.__device_list["FUEL_GAUGE"][DEVICE]

    # ABSTRACT METHOD #
    def APPLY_MAGNETIC_CONTROL(self) -> None:
        """CONTROL_COILS: Control the coils on the CubeSat, depending on the control mode (identiical for all coils)."""
        raise NotImplementedError("CubeSats must implement the control coils method")

    def TORQUE_DRIVERS_AVAILABLE(self, dir: str) -> bool:
        """Returns True if the specific torque driver for the given direction is available.

        :param dir: The direction key (e.g., 'XP', 'XM', etc.)
        :return: bool - True if the driver exists and is not None, False otherwise.
        """
        return dir in self.__torque_drivers and self.__torque_drivers[dir] is not None

    @property
    def LIGHT_SENSORS(self):
        """Returns a dictionary of light sensors with the direction as the key (e.g. 'XP', 'XM', 'YP', 'YM', 'ZM')"""
        return self.__light_sensors

    def LIGHT_SENSOR_AVAILABLE(self, dir: str) -> bool:
        """Returns True if the specific light sensor for the given direction is available.

        :param dir: The direction key (e.g., 'XP', 'XM', etc.)
        :return: bool - True if the sensor exists and is not None, False otherwise.
        """
        return dir in self.__light_sensors and self.__light_sensors[dir] is not None

    @property
    def RTC(self):
        """RTC: Returns the RTC object
        :return: object or None
        """
        return self.__device_list["RTC"][DEVICE]

    @property
    def RTC_AVAILABLE(self) -> bool:
        """RTC_AVAILABLE: Returns True if the RTC is available
        :return: bool
        """
        return self.__device_list["RTC"][DEVICE] is not None

    @property
    def RADIO(self):
        """RADIO: Returns the radio object
        :return: object or None
        """
        return self.__device_list["RADIO"][DEVICE]

    @property
    def RADIO_AVAILABLE(self) -> bool:
        """RADIO_AVAILABLE: Returns True if the radio is available
        :return: bool
        """
        return self.__device_list["RADIO"][DEVICE] is not None

    @property
    def BURN_WIRES(self):
        """BURN_WIRES: Returns the burn wire object
        :return: object or None
        """
        return self.__burn_wires

    @property
    def BURN_WIRES_AVAILABLE(self) -> bool:
        """BURN_WIRES_AVAILABLE: Returns True if the burn wires are available
        :return: bool
        """
        return self.__burn_wires is not None

    @property
    def SD_CARD(self):
        """SD_CARD: Returns the SD card object
        :return: object or None
        """
        return self.__device_list["SDCARD"][DEVICE]

    @property
    def SD_CARD_AVAILABLE(self) -> bool:
        """SD_CARD_AVAILABLE: Returns True if the SD card is available
        :return: bool
        """
        return self.__device_list["SDCARD"][DEVICE] is not None

    @property
    def VFS(self):
        """VFS: Returns the VFS object
        :return: object or None
        """
        return self.__vfs

    @property
    def VFS_AVAILABLE(self) -> bool:
        """VFS_AVAILABLE: Returns True if the VFS is available
        :return: bool
        """
        return self.__vfs is not None

    @property
    def PAYLOADUART(self):
        """PAYLOAD_EN: Returns the payload enable object
        :return: object or None
        """
        return self.__payload_uart

    @property
    def PAYLOADUART_AVAILABLE(self) -> bool:
        """PAYLOADUART_AVAILABLE: Returns True if the payload UART is available
        :return: bool
        """
        return self.__payload_uart is not None

    @property
    def BOOTTIME(self):
        """BOOTTIME: Returns the reference count since the board booted
        :return: object or None
        """
        return self._time_ref_boot

    def reboot_peripheral(self, peripheral: object) -> int:
        """REBOOT_PERIPHERAL: Reboot the peripheral"""
        raise NotImplementedError("CubeSats must implement reboot peripheral method")
