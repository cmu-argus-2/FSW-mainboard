import time

from hal.drivers.middleware.errors import Errors
from hal.drivers.middleware.generic_driver import Driver


class CubeSat:
    """CubeSat: Base class for all CubeSat implementations"""

    def __init__(self):
        # List of successfully initialized devices
        self.__device_list: list[Driver] = []

        # List of errors from most recent system diagnostic test
        self.__recent_errors: list[int] = [Errors.NOERROR]

        # State flags
        self.__state_flags = None

        # Interfaces
        self.__uart1 = None
        self.__uart2 = None
        self.__spi = None
        self.__i2c1 = None
        self.__i2c2 = None

        # Devices
        self.__gps = None
        self.__battery_monitor = None
        self.__jetson_monitor = None
        self.__imu = None
        self.__charger = None
        self.__torque_x = None
        self.__torque_y = None
        self.__torque_z = None
        self.__light_sensor_xp = None
        self.__light_sensor_xm = None
        self.__light_sensor_yp = None
        self.__light_sensor_ym = None
        self.__light_sensor_zm = None
        self.__rtc = None
        self.__radio = None
        self.__sd_card = None
        self.__burn_wires = None
        self.__vfs = None
        self.__payload_uart = None

        # Debugging
        self._time_ref_boot = int(time.time())

    ## ABSTRACT METHOD ##
    def boot_sequence(self) -> list[int]:
        """boot_sequence: Boot sequence for the CubeSat."""
        raise NotImplementedError("CubeSats must implement boot method")

    ## ABSTRACT METHOD ##
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

    ######################### INTERFACES #########################

    @property
    def UART1(self):
        """UART: Returns the UART interface"""
        return self.__uart1

    @property
    def UART2(self):
        """UART2: Returns the UART2 interface"""
        return self.__uart2

    @property
    def SPI(self):
        """SPI: Returns the SPI interface"""
        return self.__spi

    @property
    def I2C1(self):
        """I2C: Returns the I2C interface"""
        return self.__i2c1

    @property
    def I2C2(self):
        """I2C2: Returns the I2C2 interface"""
        return self.__i2c2

    ######################### DEVICES #########################

    @property
    def GPS(self):
        """GPS: Returns the gps object
        :return: object or None
        """
        return self.__gps

    @property
    def BATTERY_POWER_MONITOR(self):
        """BATTERY_POWER_MONITOR: Returns the battery power monitor object
        :return: object or None
        """
        return self.__battery_monitor

    @property
    def JETSON_POWER_MONITOR(self):
        """JETSON_MONITOR: Returns the Jetson monitor object
        :return: object or None
        """
        return self.__jetson_monitor

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
    def TORQUE_X(self):
        """TORQUE_X: Returns the torque driver in the x direction
        :return: object or None
        """
        return self.__torque_x

    @property
    def TORQUE_Y(self):
        """TORQUE_Y: Returns the torque driver in the y direction
        :return: object or None
        """
        return self.__torque_y

    @property
    def TORQUE_Z(self):
        """TORQUE_Z: Returns the torque driver in the z direction
        :return: object or None
        """
        return self.__torque_z

    @property
    def LIGHT_SENSOR_XP(self):
        """LIGHT_SENSOR_XP: Returns the light sensor in the x+ direction
        :return: object or None
        """
        return self.__light_sensor_xp

    @property
    def LIGHT_SENSOR_XM(self):
        """LIGHT_SENSOR_XM: Returns the light sensor in the x- direction
        :return: object or None
        """
        return self.__light_sensor_xm

    @property
    def LIGHT_SENSOR_YP(self):
        """LIGHT_SENSOR_YP: Returns the light sensor in the y+ direction
        :return: object or None
        """
        return self.__light_sensor_yp

    @property
    def LIGHT_SENSOR_YM(self):
        """LIGHT_SENSOR_YM: Returns the light sensor in the y- direction
        :return: object or None
        """
        return self.__light_sensor_ym

    @property
    def LIGHT_SENSOR_ZM(self):
        """LIGHT_SENSOR_ZM: Returns the light sensor in the z+ direction
        :return: object or None
        """
        return self.__light_sensor_zm

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
