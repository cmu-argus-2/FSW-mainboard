import time

from hal.drivers.middleware.errors import Errors


class CubeSat:
    """CubeSat: Base class for all CubeSat implementations"""

    __slots__ = (
        "__device_list",
        "__recent_errors",
        "__state_flags",
        "__payload_uart",
        "_time_ref_boot",
    )

    def __init__(self):
        self.__device_list = {
            "SDCARD": Device(self.__sd_card_boot),
            "IMU": Device(self.__imu_boot),
            "RTC": Device(self.__rtc_boot),
            # "GPS": Device(self.__gps_boot),
            # "RADIO": Device(self.__radio_boot),
            # "FUEL_GAUGE": Device(self.__fuel_gauge_boot),
            # "BURN_WIRE": Device(self.__burn_wire_boot),
            "BOARD_PWR": Device(self.__power_monitor_boot),
            # "RADIO_PWR": Device(self.__power_monitor_boot),
            # "JETSON_PWR": Device(self.__power_monitor_boot),
            # "XP_PWR": Device(self.__power_monitor_boot),
            # "XM_PWR": Device(self.__power_monitor_boot),
            # "YP_PWR": Device(self.__power_monitor_boot),
            # "YM_PWR": Device(self.__power_monitor_boot),
            # "ZP_PWR": Device(self.__power_monitor_boot),
            # "ZM_PWR": Device(self.__power_monitor_boot),
            # "TORQUE_XP": Device(self.__torque_driver_boot),
            # "TORQUE_XM": Device(self.__torque_driver_boot),
            # "TORQUE_YP": Device(self.__torque_driver_boot),
            # "TORQUE_YM": Device(self.__torque_driver_boot),
            # "TORQUE_ZP": Device(self.__torque_driver_boot),
            # "TORQUE_ZM": Device(self.__torque_driver_boot),
            # "LIGHT_XP": Device(self.__light_sensor_boot),
            # "LIGHT_XM": Device(self.__light_sensor_boot),
            # "LIGHT_YP": Device(self.__light_sensor_boot),
            # "LIGHT_YM": Device(self.__light_sensor_boot),
            # "LIGHT_ZM": Device(self.__light_sensor_boot),
            # "SUN1": Device(self.__light_sensor_boot),
            # "SUN2": Device(self.__light_sensor_boot),
            # "SUN3": Device(self.__light_sensor_boot),
            # "SUN4": Device(self.__light_sensor_boot),
        }

        # List of errors from most recent system diagnostic test
        self.__recent_errors: list[int] = [Errors.NOERROR]

        # State flags
        # self.__state_flags = None

        self.__imu_temp_flag = False

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

    @property
    def ERRORS(self):
        """ERRORS: Returns the errors object
        :return: object or None
        """
        error_list = {}
        for name, device in self.__device_list.items():
            if device.error != Errors.NOERROR:
                error_list[name] = device.device
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
        return self.__device_list["GPS"].device

    @property
    def GPS_AVAILABLE(self) -> bool:
        """GPS_AVAILABLE: Returns True if the GPS is available
        :return: bool
        """
        return self.__device_list["GPS"].device is not None

    @property
    def POWER_MONITORS(self):
        """POWER_MONITORS: Returns the power monitor object
        :return: object or None
        """
        power_monitors = {}
        for name, device in self.__device_list.items():
            if "_PWR" in name:
                power_monitors[name.replace("_PWR", "")] = device.device
        return power_monitors

    def POWER_MONITOR_AVAILABLE(self, dir: str) -> bool:
        """POWER_MONITOR_AVAILABLE: Returns True if the power monitor for the given direction is available
        :return: bool
        """
        return self.__device_list[dir + "_PWR"].device is not None

    @property
    def IMU(self):
        """IMU: Returns the IMU object
        :return: object or None
        """
        return self.__device_list["IMU"].device

    @property
    def IMU_AVAILABLE(self) -> bool:
        """IMU_AVAILABLE: Returns True if the IMU is available
        :return: bool
        """
        return self.__device_list["IMU"].device is not None

    @property
    def IMU_TEMPERATURE_AVAILABLE(self) -> bool:
        """IMU_AVAILABLE: Returns True if the IMU is available
        :return: bool
        """
        return self.__imu_temp_flag

    # @property
    # def CHARGER(self):
    #     """CHARGER: Returns the charger object
    #     :return: object or None
    #     """
    #     return self.__charger

    # @property
    # def CHARGER_AVAILABLE(self) -> bool:
    #     """CHARGER_AVAILABLE: Returns True if the charger is available
    #     :return: bool
    #     """
    #     return self.__charger is not None

    @property
    def TORQUE_XP_POWER_MONITOR(self):
        """TORQUE_XP: Returns the torque driver in the x+ direction
        :return: object or None
        """
        return self.__device_list["TORQUE_XP"].device

    # @property
    # def TORQUE_XP_POWER_MONITOR_AVAILABLE(self) -> bool:
    #     """TORQUE_XP_POWER_MONITOR_AVAILABLE: Returns True if the torque driver in the x+ direction is available
    #     :return: bool
    #     """
    #     return self.__device_list["TORQUE_XP"].device is not None

    @property
    def TORQUE_DRIVERS(self):
        """Returns a dictionary of torque drivers with the direction as the key (e.g. 'XP', 'XM', 'YP', 'YM', 'ZM')"""
        torque_drivers = {}
        for name, device in self.__device_list.items():
            if "TORQUE_" in name:
                torque_drivers[name.replace("TORQUE_", "")] = device.device
        return torque_drivers

    @property
    def FUEL_GAUGE(self):
        """FUEL_GAUGE: Returns the fuel gauge object
        :return: object or None
        """
        return self.__device_list["FUEL_GAUGE"].device

    # ABSTRACT METHOD #
    def APPLY_MAGNETIC_CONTROL(self, dir: str, throttle: float) -> None:
        """CONTROL_COILS: Control the coils on the CubeSat, depending on the control mode (identiical for all coils)."""
        if self.TORQUE_DRIVERS_AVAILABLE(dir):
            self.__torque_drivers[dir].set_throttle(throttle)

    def TORQUE_DRIVERS_AVAILABLE(self, dir: str) -> bool:
        """Returns True if the specific torque driver for the given direction is available.

        :param dir: The direction key (e.g., 'XP', 'XM', etc.)
        :return: bool - True if the driver exists and is not None, False otherwise.
        """
        return self.device_list["TORQUE_" + dir].device is not None

    @property
    def LIGHT_SENSORS(self):
        """Returns a dictionary of light sensors with the direction as the key (e.g. 'XP', 'XM', 'YP', 'YM', 'ZM')"""
        light_sensors = {}
        for name, device in self.__device_list.items():
            if "LIGHT_" in name:
                light_sensors[name.replace("LIGHT_", "")] = device.device
        return light_sensors

    def LIGHT_SENSOR_AVAILABLE(self, dir: str) -> bool:
        """Returns True if the specific light sensor for the given direction is available.

        :param dir: The direction key (e.g., 'XP', 'XM', etc.)
        :return: bool - True if the sensor exists and is not None, False otherwise.
        """
        return self.__device_list["LIGHT_" + dir].device is not None

    @property
    def RTC(self):
        """RTC: Returns the RTC object
        :return: object or None
        """
        return self.__device_list["RTC"].device

    @property
    def RTC_AVAILABLE(self) -> bool:
        """RTC_AVAILABLE: Returns True if the RTC is available
        :return: bool
        """
        return self.__device_list["RTC"].device is not None

    @property
    def RADIO(self):
        """RADIO: Returns the radio object
        :return: object or None
        """
        return self.__device_list["RADIO"].device

    @property
    def RADIO_AVAILABLE(self) -> bool:
        """RADIO_AVAILABLE: Returns True if the radio is available
        :return: bool
        """
        return self.__device_list["RADIO"].device is not None

    @property
    def BURN_WIRES(self):
        """BURN_WIRES: Returns the burn wire object
        :return: object or None
        """
        return self.__device_list["BURN_WIRES"].device

    @property
    def BURN_WIRES_AVAILABLE(self) -> bool:
        """BURN_WIRES_AVAILABLE: Returns True if the burn wires are available
        :return: bool
        """
        return self.__device_list["BURN_WIRES"].device is not None

    @property
    def SD_CARD(self):
        """SD_CARD: Returns the SD card object
        :return: object or None
        """
        return self.__device_list["SDCARD"].device

    @property
    def SD_CARD_AVAILABLE(self) -> bool:
        """SD_CARD_AVAILABLE: Returns True if the SD card is available
        :return: bool
        """
        return self.__device_list["SDCARD"].device is not None

    # @property
    # def VFS(self):
    #     """VFS: Returns the VFS object
    #     :return: object or None
    #     """
    #     return self.__vfs

    # @property
    # def VFS_AVAILABLE(self) -> bool:
    #     """VFS_AVAILABLE: Returns True if the VFS is available
    #     :return: bool
    #     """
    #     return self.__vfs is not None

    # @property
    # def PAYLOADUART(self):
    #     """PAYLOAD_EN: Returns the payload enable object
    #     :return: object or None
    #     """
    #     return self.__payload_uart

    # @property
    # def PAYLOADUART_AVAILABLE(self) -> bool:
    #     """PAYLOADUART_AVAILABLE: Returns True if the payload UART is available
    #     :return: bool
    #     """
    #     return self.__payload_uart is not None

    @property
    def BOOTTIME(self):
        """BOOTTIME: Returns the reference count since the board booted
        :return: object or None
        """
        return self._time_ref_boot

    def reboot_peripheral(self, peripheral: object) -> int:
        """REBOOT_PERIPHERAL: Reboot the peripheral"""
        raise NotImplementedError("CubeSats must implement reboot peripheral method")


class Device:
    def __init__(self, boot_fn: object, device: object = None, error: int = 0):
        self.device = device
        self.error = error
        self.boot_fn = boot_fn
