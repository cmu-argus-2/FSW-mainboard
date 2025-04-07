import time
from collections import OrderedDict

from hal.drivers.middleware.errors import Errors


class Device:
    def __init__(self, boot_fn: object, device: object = None, error: int = 0):
        self.device = device
        self.error = error
        self.boot_fn = boot_fn


class CubeSat:
    """CubeSat: Base class for all CubeSat implementations"""

    __slots__ = (
        "__device_list",
        "__payload_uart",
        "_time_ref_boot",
    )

    def __new__(cls, *args, **kwargs):
        if cls is CubeSat:
            raise TypeError(f"{cls.__name__} is a static base class and cannot be instantiated.")
        return super().__new__(cls)

    def __init__(self):
        self.__device_list = OrderedDict(
            [
                ("NEOPIXEL", Device(self.__neopixel_boot)),
                ("SDCARD", Device(self.__sd_card_boot)),  # SD Card must enabled before other devices
                ("RTC", Device(self.__rtc_boot)),
                ("GPS", Device(self.__gps_boot)),
                ("RADIO", Device(self.__radio_boot)),
                ("FUEL_GAUGE", Device(self.__fuel_gauge_boot)),
                # ("BURN_WIRE", Device(self.__burn_wire_boot)),
                ("BOARD_PWR", Device(self.__power_monitor_boot)),
                ("RADIO_PWR", Device(self.__power_monitor_boot)),
                ("GPS_PWR", Device(self.__power_monitor_boot)),
                # ("JETSON_PWR", Device(self.__power_monitor_boot)),
                ("XP_PWR", Device(self.__power_monitor_boot)),
                ("XM_PWR", Device(self.__power_monitor_boot)),
                ("YP_PWR", Device(self.__power_monitor_boot)),
                ("YM_PWR", Device(self.__power_monitor_boot)),
                ("ZP_PWR", Device(self.__power_monitor_boot)),
                ("TORQUE_XP", Device(self.__torque_driver_boot)),
                ("TORQUE_XM", Device(self.__torque_driver_boot)),
                ("TORQUE_YP", Device(self.__torque_driver_boot)),
                ("TORQUE_YM", Device(self.__torque_driver_boot)),
                ("TORQUE_ZP", Device(self.__torque_driver_boot)),
                ("TORQUE_ZM", Device(self.__torque_driver_boot)),
                ("LIGHT_XP", Device(self.__light_sensor_boot)),
                ("LIGHT_XM", Device(self.__light_sensor_boot)),
                ("LIGHT_YP", Device(self.__light_sensor_boot)),
                ("LIGHT_YM", Device(self.__light_sensor_boot)),
                ("LIGHT_ZM", Device(self.__light_sensor_boot)),
                # ("LIGHT_ZP_1", Device(self.__light_sensor_boot)),
                # ("LIGHT_ZP_2", Device(self.__light_sensor_boot)),
                # ("LIGHT_ZP_3", Device(self.__light_sensor_boot)),
                # ("LIGHT_ZP_4", Device(self.__light_sensor_boot)),
                ("IMU", Device(self.__imu_boot)),
            ]
        )

        self.__imu_temp_flag = False

        # Get boot time from time.monotonic()
        self._time_ref_boot = int(time.monotonic())

    # ABSTRACT METHOD #
    def boot_sequence(self) -> list[int]:
        """boot_sequence: Boot sequence for the CubeSat."""
        raise NotImplementedError("CubeSats must implement boot method")

    def append_device(self, device_name: str, boot_fn: object, device: object = None, error: int = 0) -> None:
        """append_device: Append a device to the device list"""
        self.__device_list[device_name] = Device(boot_fn, device, error)

    @property
    def ERRORS(self):
        """ERRORS: Returns the errors object
        :return: object or None
        """
        error_list = {}
        for name, device in self.__device_list.items():
            if device.error != Errors.NOERROR:
                error_list[name] = device.error
        return error_list

    def key_in_device_list(self, key: str) -> bool:
        """key_in_device_list: Check if the key is in the device list"""
        return key in self.__device_list

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
        return self.key_in_device_list("GPS") and self.__device_list["GPS"].device is not None

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
        return self.key_in_device_list(dir + "_PWR") and self.__device_list[dir + "_PWR"].device is not None

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
        return self.key_in_device_list("IMU") and self.__device_list["IMU"].device is not None

    @property
    def IMU_TEMPERATURE_AVAILABLE(self) -> bool:
        """IMU_AVAILABLE: Returns True if the IMU is available
        :return: bool
        """
        return self.__imu_temp_flag

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
        return self.key_in_device_list("TORQUE_" + dir) and self.__device_list["TORQUE_" + dir].device is not None

    def TORQUE_DRIVERS_CURRENT(self, dir: str) -> float:
        """Returns the coil current for the specific magnetorquer if available and returns -1 otherwise

        :param dir: The direction key (e.g., 'XP', 'XM', etc.)
        :return: float - current value in amps if the coil is available else -1
        """
        if self.TORQUE_DRIVERS_AVAILABLE(dir):
            self.__device_list["TORQUE_" + dir].device.read_current()
        else:
            return -1.0

    def TORQUE_DRIVERS_VOLTAGE(self, dir: str) -> float:
        """Returns the coil voltage for the specific magnetorquer if available and returns -1 otherwise

        :param dir: The direction key (e.g., 'XP', 'XM', etc.)
        :return: float - voltage value in volts if the coil is available else -1
        """
        if self.TORQUE_DRIVERS_AVAILABLE(dir):
            self.__device_list["TORQUE_" + dir].device.read_voltage()
        else:
            return -1.0

    # ABSTRACT METHOD #
    def APPLY_MAGNETIC_CONTROL(self, dir: str, throttle: float) -> None:
        """CONTROL_COILS: Control the coils on the CubeSat, depending on the control mode (identiical for all coils)."""
        if self.TORQUE_DRIVERS_AVAILABLE(dir):
            self.__device_list["TORQUE_" + dir].device.set_throttle(throttle)

    @property
    def FUEL_GAUGE(self):
        """FUEL_GAUGE: Returns the fuel gauge object
        :return: object or None
        """
        return self.__device_list["FUEL_GAUGE"].device

    @property
    def FUEL_GAUGE_AVAILABLE(self) -> bool:
        """FUEL_GAUGE_AVAILABLE: Returns True if the fuel gauge is available
        :return: bool
        """
        return self.key_in_device_list("FUEL_GAUGE") and self.__device_list["FUEL_GAUGE"].device is not None

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
        return self.key_in_device_list("LIGHT_" + dir) and self.__device_list["LIGHT_" + dir].device is not None

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
        return self.key_in_device_list("RTC") and self.__device_list["RTC"].device is not None

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
        return self.key_in_device_list("RADIO") and self.__device_list["RADIO"].device is not None

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
        return self.key_in_device_list("BURN_WIRES") and self.__device_list["BURN_WIRES"].device is not None

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
        return self.key_in_device_list("SDCARD") and self.__device_list["SDCARD"].device is not None

    @property
    def NEOPIXEL(self):
        """NEOPIXEL: Returns the neopixel object
        :return: object or None
        """
        return self.__device_list["NEOPIXEL"].device

    @property
    def NEOPIXEL_AVAILABLE(self) -> bool:
        """NEOPIXEL_AVAILABLE: Returns True if the neopixel is available
        :return: bool
        """
        return self.key_in_device_list("NEOPIXEL") and self.__device_list["NEOPIXEL"].device is not None

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
