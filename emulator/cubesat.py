import time
from typing import List, Optional

from hal.drivers.diagnostics.diagnostics import Diagnostics


class CubeSat:
    """CubeSat: Base class for all CubeSat implementations"""

    def __init__(self):
        # List of successfully initialized devices
        self._device_list: List[Diagnostics] = []

        # List of errors from most recent system diagnostic test
        self._recent_errors: List[int] = [Diagnostics.NOERROR]

        # State flags
        self._state_flags = None

        # Interfaces
        self._uart1 = None
        self._uart2 = None
        self._spi = None
        self._i2c1 = None
        self._i2c2 = None

        # Devices
        self._imu_temp_flag = False
        self._payload_uart = None
        self.__device_list = {
            "SDCARD": Device(self.__sd_card_boot),
            "IMU": Device(self.__imu_boot),
            "RTC": Device(self.__rtc_boot),
            "GPS": Device(self.__gps_boot),
            "RADIO": Device(self.__radio_boot),
            "FUEL_GAUGE": Device(self.__fuel_gauge_boot),
            "BURN_WIRE": Device(self.__burn_wire_boot),
            "BOARD_PWR": Device(self.__power_monitor_boot),
            "RADIO_PWR": Device(self.__power_monitor_boot),
            "JETSON_PWR": Device(self.__power_monitor_boot),
            "XP_PWR": Device(self.__power_monitor_boot),
            "XM_PWR": Device(self.__power_monitor_boot),
            "YP_PWR": Device(self.__power_monitor_boot),
            "YM_PWR": Device(self.__power_monitor_boot),
            "ZP_PWR": Device(self.__power_monitor_boot),
            "ZM_PWR": Device(self.__power_monitor_boot),
            "TORQUE_XP": Device(self.__torque_driver_boot),
            "TORQUE_XM": Device(self.__torque_driver_boot),
            "TORQUE_YP": Device(self.__torque_driver_boot),
            "TORQUE_YM": Device(self.__torque_driver_boot),
            "TORQUE_ZP": Device(self.__torque_driver_boot),
            "TORQUE_ZM": Device(self.__torque_driver_boot),
            "LIGHT_XP": Device(self.__light_sensor_boot),
            "LIGHT_XM": Device(self.__light_sensor_boot),
            "LIGHT_YP": Device(self.__light_sensor_boot),
            "LIGHT_YM": Device(self.__light_sensor_boot),
            "LIGHT_ZM": Device(self.__light_sensor_boot),
            "SUN1": Device(self.__light_sensor_boot),
            "SUN2": Device(self.__light_sensor_boot),
            "SUN3": Device(self.__light_sensor_boot),
            "SUN4": Device(self.__light_sensor_boot),
        }

        # Debugging
        self._time_ref_boot = int(time.time())

    # ABSTRACT METHOD #
    def boot_sequence(self) -> List[int]:
        """boot_sequence: Boot sequence for the CubeSat."""
        raise NotImplementedError("CubeSats must implement boot method")

    # ABSTRACT METHOD #
    def run_system_diagnostics(self) -> Optional[List[int]]:
        """run_diagnostic_test: Run all tests for the component"""
        raise NotImplementedError("CubeSats must implement diagnostics method")

    def get_recent_errors(self) -> List[int]:
        """get_recent_errors: Get the most recent errors from the system"""
        return self._recent_errors

    @property
    def device_list(self):
        """device_list: Get the list of successfully initialized devices"""
        return self._device_list

    @property
    def ERRORS(self):
        """ERRORS: Returns the errors object
        :return: object or None
        """
        error_list = {}
        for name, device in self.__device_list.items():
            if device.error != 0:
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
    def BOARD_POWER_MONITOR(self):
        """BOARD_POWER_MONITOR: Returns the board power monitor object
        :return: object or None
        """
        return self.__device_list["BOARD_PWR"].device

    @property
    def BOARD_POWER_MONITOR_AVAILABLE(self) -> bool:
        """BOARD_POWER_MONITOR_AVAILABLE: Returns True if the board power monitor is available
        :return: bool
        """
        return self.__device_list["BOARD_PWR"].device is not None

    @property
    def JETSON_POWER_MONITOR(self):
        """JETSON_MONITOR: Returns the Jetson monitor object
        :return: object or None
        """
        return self.__device_list["JETSON_PWR"].device

    @property
    def JETSON_POWER_MONITOR_AVAILABLE(self) -> bool:
        """JETSON_POWER_MONITOR_AVAILABLE: Returns True if the Jetson power monitor is available
        :return: bool
        """
        return self.__device_list["JETSON_PWR"].device is not None

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
        return self._imu_temp_flag

    @property
    def FUEL_GAUGE(self):
        """FUEL_GAUGE: Returns the fuel gauge object
        :return: object or None
        """
        return self.__device_list["FUEL_GAUGE"].device

    @property
    def TORQUE_DRIVERS(self):
        """Returns a dictionary of torque drivers with the direction as the key (e.g. 'XP', 'XM', 'YP', 'YM', 'ZM')"""
        torque_drivers = {}
        for name, device in self.__device_list.items():
            if "TORQUE_" in name:
                torque_drivers[name.replace("TORQUE_", "")] = device.device
        return torque_drivers

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
                light_sensors[name] = device.device
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
        return self._sd_card

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

    @property
    def PAYLOADUART(self):
        """PAYLOAD_EN: Returns the payload enable object
        :return: object or None
        """
        return self._payload_uart

    @property
    def PAYLOADUART_AVAILABLE(self) -> bool:
        """PAYLOADUART_AVAILABLE: Returns True if the payload UART is available
        :return: bool
        """
        return self._payload_uart is not None

    @property
    def BOOTTIME(self):
        """BOOTTIME: Returns the reference count since the board booted
        :return: object or None
        """
        return self._time_ref_boot


class Device:
    def __init__(self, boot_fn: object, device: object = None, error: int = 0):
        self.device = device
        self.error = error
        self.boot_fn = boot_fn
