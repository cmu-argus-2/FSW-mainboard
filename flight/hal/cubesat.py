import time
from collections import OrderedDict

from hal.drivers.errors import Errors
from micropython import const

# Argus Safety Integrity Level
ASIL0 = const(0)  # debug components, should not be in flight and do not care if error
ASIL1 = const(1)
ASIL2 = const(2)
ASIL3 = const(3)
ASIL4 = const(4)


class Device:
    def __init__(
        self,
        boot_fn: object,
        ASIL: int,
        peripheral_line: bool = True,
        device: object = None,
        error: int = Errors.NO_ERROR,
    ) -> None:
        self.device = device
        self.error = error
        self.boot_fn = boot_fn
        self.ASIL = ASIL
        self.error_count = 0
        self.peripheral_line = peripheral_line
        self.dead = False
        self.temp_disabled = False


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
                ("NEOPIXEL", Device(self.__neopixel_boot, ASIL0)),
                ("SDCARD", Device(self.__sd_card_boot, ASIL1)),  # SD Card must enabled before other devices
                ("RTC", Device(self.__rtc_boot, ASIL2)),
                ("GPS", Device(self.__gps_boot, ASIL4, peripheral_line=False)),
                ("RADIO", Device(self.__radio_boot, ASIL4, peripheral_line=False)),
                ("IMU", Device(self.__imu_boot, ASIL3)),
                ("FUEL_GAUGE", Device(self.__fuel_gauge_boot, ASIL2)),
                ("BATT_HEATERS", Device(self.__battery_heaters_boot, ASIL4, peripheral_line=False)),
                ("WATCHDOG", Device(self.__watchdog_boot, ASIL4)),
                ("BURN_WIRES", Device(self.__burn_wire_boot, ASIL4)),
                ("BOARD_PWR", Device(self.__power_monitor_boot, ASIL1)),
                ("RADIO_PWR", Device(self.__power_monitor_boot, ASIL1)),
                ("GPS_PWR", Device(self.__power_monitor_boot, ASIL1)),
                ("JETSON_PWR", Device(self.__power_monitor_boot, ASIL1)),
                ("XP_PWR", Device(self.__power_monitor_boot, ASIL1)),
                ("XM_PWR", Device(self.__power_monitor_boot, ASIL1)),
                ("YP_PWR", Device(self.__power_monitor_boot, ASIL1)),
                ("YM_PWR", Device(self.__power_monitor_boot, ASIL1)),
                ("ZP_PWR", Device(self.__power_monitor_boot, ASIL1)),
                ("TORQUE_XP", Device(self.__torque_driver_boot, ASIL3)),
                ("TORQUE_XM", Device(self.__torque_driver_boot, ASIL3)),
                ("TORQUE_YP", Device(self.__torque_driver_boot, ASIL3)),
                ("TORQUE_YM", Device(self.__torque_driver_boot, ASIL3)),
                ("TORQUE_ZP", Device(self.__torque_driver_boot, ASIL3)),
                ("TORQUE_ZM", Device(self.__torque_driver_boot, ASIL3)),
                ("LIGHT_XP", Device(self.__light_sensor_boot, ASIL2)),
                ("LIGHT_XM", Device(self.__light_sensor_boot, ASIL2)),
                ("LIGHT_YP", Device(self.__light_sensor_boot, ASIL2)),
                ("LIGHT_YM", Device(self.__light_sensor_boot, ASIL2)),
                ("LIGHT_ZM", Device(self.__light_sensor_boot, ASIL2)),
                ("LIGHT_ZP_1", Device(self.__light_sensor_boot, ASIL2)),
                ("LIGHT_ZP_2", Device(self.__light_sensor_boot, ASIL2)),
                ("LIGHT_ZP_3", Device(self.__light_sensor_boot, ASIL2)),
                ("LIGHT_ZP_4", Device(self.__light_sensor_boot, ASIL2)),
                ("DEPLOYMENT_XP", Device(self.__deployment_sensor_boot, ASIL1)),
                ("DEPLOYMENT_YM", Device(self.__deployment_sensor_boot, ASIL1)),
            ]
        )

        self.__imu_temp_flag = False
        self.__errors = {
            "SDCARD": [],
            "RTC": [],
            "GPS": [],
            "RADIO": [],
            "IMU": [],
            "FUEL_GAUGE": [],
            "BATT_HEATERS": [],
            "WATCHDOG": [],
            "BURN_WIRES": [],
            "BOARD_PWR": [],
            "RADIO_PWR": [],
            "GPS_PWR": [],
            "JETSON_PWR": [],
            "XP_PWR": [],
            "XM_PWR": [],
            "YP_PWR": [],
            "YM_PWR": [],
            "ZP_PWR": [],
            "TORQUE_XP": [],
            "TORQUE_XM": [],
            "TORQUE_YP": [],
            "TORQUE_YM": [],
            "TORQUE_ZP": [],
            "TORQUE_ZM": [],
            "LIGHT_XP": [],
            "LIGHT_XM": [],
            "LIGHT_YP": [],
            "LIGHT_YM": [],
            "LIGHT_ZM": [],
            "LIGHT_ZP_1": [],
            "LIGHT_ZP_2": [],
            "LIGHT_ZP_3": [],
            "LIGHT_ZP_4": [],
            "DEPLOYMENT_XP": [],
            "DEPLOYMENT_YM": [],
        }
        # Get boot time from time.monotonic()
        self._time_ref_boot = int(time.monotonic())

    # ABSTRACT METHOD #
    def boot_sequence(self) -> list[int]:
        """boot_sequence: Boot sequence for the CubeSat."""
        raise NotImplementedError("CubeSats must implement boot method")

    def print_device_list(self) -> None:
        """print_device_list: Print the device list."""
        for name, device in self.__device_list.items():
            print(f"{name}: {device.device}")

    def print_device_status(self) -> None:
        """print_device_status: Print the device status."""
        for name, device in self.__device_list.items():
            print(f"{name}: {device.device} - {device.error} - {device.dead} - {device.temp_disabled}")

    @property
    def ERRORS(self):
        """ERRORS: Returns the errors object
        :return: object or None
        """
        error_list = {}
        for name, device in self.__device_list.items():
            if device.error != Errors.NO_ERROR and device.dead is False:
                error_list[name] = device.error
        return error_list

    @property
    def DEVICES_STATUS(self):
        """DEVICES_STATUS: Returns the status of the devices"""
        status = {}
        for name, device in self.__device_list.items():
            if device.ASIL != ASIL0:
                status[name] = [device.error, device.error_count, device.dead]
        return status

    def update_device_error(self, device_name: str, error: int):
        """update_device_error: Update the error for the given device."""
        if device_name in self.__device_list:
            self.__device_list[device_name].error = error

    def update_device_error_count(self, device_name: str, error_count: int):
        """update_device_error_count: Update the error count for the given device."""
        if device_name in self.__device_list:
            self.__device_list[device_name].error_count = error_count

    def increment_device_error_count(self, device_name: str):
        """increment_device_error_count: Increment the error count for the given device."""
        if device_name in self.__device_list:
            self.__device_list[device_name].error_count += 1

    def get_error_count(self, device_name: str) -> int:
        """get_error_count: Get the error count for the given device."""
        if device_name in self.__device_list:
            return self.__device_list[device_name].error_count
        return None

    def update_device_dead(self, device_name: str, dead: bool):
        """update_device_dead: Update the dead status for the given device."""
        if device_name in self.__device_list:
            self.__device_list[device_name].dead = dead

    def get_device_dead(self, device_name: str) -> bool:
        """get_device_dead: Get the dead status for the given device."""
        if device_name in self.__device_list:
            return self.__device_list[device_name].dead
        return True

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
        return (
            self.key_in_device_list("GPS")
            and self.__device_list["GPS"].device is not None
            and not self.__device_list["GPS"].dead
            and not self.__device_list["GPS"].temp_disabled
        )

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
        return (
            self.key_in_device_list(dir + "_PWR")
            and self.__device_list[dir + "_PWR"].device is not None
            and not self.__device_list[dir + "_PWR"].dead
            and not self.__device_list[dir + "_PWR"].temp_disabled
        )

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
        return (
            self.key_in_device_list("IMU")
            and self.__device_list["IMU"].device is not None
            and not self.__device_list["IMU"].dead
            and not self.__device_list["IMU"].temp_disabled
        )

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
        return (
            self.key_in_device_list("TORQUE_" + dir)
            and self.__device_list["TORQUE_" + dir].device is not None
            and not self.__device_list["TORQUE_" + dir].dead
            and not self.__device_list["TORQUE_" + dir].temp_disabled
        )

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
        return (
            self.key_in_device_list("FUEL_GAUGE")
            and self.__device_list["FUEL_GAUGE"].device is not None
            and not self.__device_list["FUEL_GAUGE"].dead
            and not self.__device_list["FUEL_GAUGE"].temp_disabled
        )

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
        return (
            self.key_in_device_list("LIGHT_" + dir)
            and self.__device_list["LIGHT_" + dir].device is not None
            and not self.__device_list["LIGHT_" + dir].dead
            and not self.__device_list["LIGHT_" + dir].temp_disabled
        )

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
        return (
            self.key_in_device_list("RTC")
            and self.__device_list["RTC"].device is not None
            and not self.__device_list["RTC"].dead
            and not self.__device_list["RTC"].temp_disabled
        )

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
        return (
            self.key_in_device_list("RADIO")
            and self.__device_list["RADIO"].device is not None
            and not self.__device_list["RADIO"].dead
            and not self.__device_list["RADIO"].temp_disabled
        )

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
        return (
            self.key_in_device_list("BURN_WIRES")
            and self.__device_list["BURN_WIRES"].device is not None
            and not self.__device_list["BURN_WIRES"].dead
            and not self.__device_list["BURN_WIRES"].temp_disabled
        )

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
        return (
            self.key_in_device_list("SDCARD")
            and self.__device_list["SDCARD"].device is not None
            and not self.__device_list["SDCARD"].dead
            and not self.__device_list["SDCARD"].temp_disabled
        )

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
        return (
            self.key_in_device_list("NEOPIXEL")
            and self.__device_list["NEOPIXEL"].device is not None
            and (not self.__device_list["NEOPIXEL"].dead and not self.__device_list["NEOPIXEL"].temp_disabled)
        )

    @property
    def BATTERY_HEATERS(self):
        """BATT_HEATERS: Returns the battery heaters object
        :return: object or None
        """
        return self.__device_list["BATT_HEATERS"].device

    @property
    def BATTERY_HEATERS_AVAILABLE(self) -> bool:
        """BATT_HEATERS_AVAILABLE: Returns True if the battery heaters are available
        :return: bool
        """
        return (
            self.key_in_device_list("BATT_HEATERS")
            and self.__device_list["BATT_HEATERS"].device is not None
            and not self.__device_list["BATT_HEATERS"].dead
            and not self.__device_list["BATT_HEATERS"].temp_disabled
        )

    @property
    def WATCHDOG(self):
        """WATCHDOG: Returns the watchdog object
        :return: object or None
        """
        return self.__device_list["WATCHDOG"].device

    @property
    def WATCHDOG_AVAILABLE(self) -> bool:
        """WATCHDOG_AVAILABLE: Returns True if the watchdog is available
        :return: bool
        """
        return (
            self.key_in_device_list("WATCHDOG")
            and self.__device_list["WATCHDOG"].device is not None
            and not self.__device_list["WATCHDOG"].dead
            and not self.__device_list["WATCHDOG"].temp_disabled
        )

    @property
    def DEPLOYMENT_SENSORS(self):
        """Returns a dictionary of deployment sensors with the direction as the key (e.g. 'XP', 'YM')"""
        deployment_sensors = {}
        for name, device in self.__device_list.items():
            if "DEPLOYMENT_" in name:
                deployment_sensors[name.replace("DEPLOYMENT_", "")] = device.device
        return deployment_sensors

    def DEPLOYMENT_SENSOR_AVAILABLE(self, dir: str) -> bool:
        """Returns True if the specific deployment sensor for the given direction is available.

        :param dir: The direction key (e.g., 'XP', 'YM')
        :return: bool - True if the sensor exists and is not None, False otherwise.
        """
        return self.key_in_device_list("DEPLOYMENT_" + dir) and self.__device_list["DEPLOYMENT_" + dir].device is not None

    def DEPLOYMENT_SENSOR_DISTANCE(self, dir: str) -> float:
        """Returns the distance reading for the specific deployment sensor if available and returns -1 otherwise

        :param dir: The direction key (e.g., 'XP', 'YM', etc.)
        :return: float - distance value in cm if the sensor is available else -1
        """
        if self.DEPLOYMENT_SENSOR_AVAILABLE(dir):
            return self.__device_list["DEPLOYMENT_" + dir].device.distance
        return -1

    @property
    def PAYLOADUART(self):
        """PAYLOAD_EN: Returns the payload UART object
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

    ######################## ERROR HANDLING ########################

    def handle_error(self, device_name: str) -> int:
        raise NotImplementedError("CubeSats must implement handle_error method")

    def graceful_reboot_devices(self, device_name: str):
        raise NotImplementedError("CubeSats must implement graceful_reboot_devices method")

    def reboot(self, device_name: str):
        raise NotImplementedError("CubeSats must implement reboot_devices method")

    def check_device_dead(self, error_count: int) -> bool:
        raise NotImplementedError("CubeSats must implement check_device_dead method")

    @property
    def SAMPLE_DEVICE_ERRORS(self) -> dict[str, list[int]]:
        """SAMPLE_DEVICE_ERRORS: Sample the device errors"""
        for key in self.__errors:
            self.__errors[key] = []
        for name, device in self.__device_list.items():
            if device.ASIL != ASIL0:
                if (
                    device.device is None
                    and not device.dead
                    and not device.temp_disabled
                    and device.error == Errors.DEVICE_NOT_INITIALISED
                ):
                    self.__errors[name] = [Errors.DEVICE_NOT_INITIALISED]
                elif device.device is not None and not device.dead and not device.temp_disabled:
                    try:
                        self.__errors[name] = device.device.device_errors
                    except Exception:
                        self.__errors[name] = [Errors.DEVICE_NOT_INITIALISED]
        return self.__errors
