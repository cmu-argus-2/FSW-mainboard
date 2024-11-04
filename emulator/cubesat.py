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
        self._gps = None
        self._battery_monitor = None
        self._jetson_monitor = None
        self._imu = None
        self._charger = None
        self._torque_x = None
        self._torque_y = None
        self._torque_z = None
        self._light_sensor_xp = None
        self._light_sensor_xm = None
        self._light_sensor_yp = None
        self._light_sensor_ym = None
        self._light_sensor_zm = None
        self._rtc = None
        self._radio = None
        self._sd_card = None
        self._burn_wires = None
        self._vfs = None
        self._payload_uart = None

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

    def append_device(self, device):
        """append_device: Append a device to the device list"""
        self._device_list.append(device)

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
        return self._gps

    @property
    def BATTERY_POWER_MONITOR(self):
        """BATTERY_POWER_MONITOR: Returns the battery power monitor object
        :return: object or None
        """
        return self._battery_monitor

    @property
    def JETSON_POWER_MONITOR(self):
        """JETSON_MONITOR: Returns the Jetson monitor object
        :return: object or None
        """
        return self._jetson_monitor

    @property
    def IMU(self):
        """IMU: Returns the IMU object
        :return: object or None
        """
        return self._imu

    @property
    def CHARGER(self):
        """CHARGER: Returns the charger object
        :return: object or None
        """
        return self._charger

    @property
    def TORQUE_X(self):
        """TORQUE_X: Returns the torque driver in the x direction
        :return: object or None
        """
        return self._torque_x

    @property
    def TORQUE_Y(self):
        """TORQUE_Y: Returns the torque driver in the y direction
        :return: object or None
        """
        return self._torque_y

    @property
    def TORQUE_Z(self):
        """TORQUE_Z: Returns the torque driver in the z direction
        :return: object or None
        """
        return self._torque_z

    @property
    def LIGHT_SENSOR_XP(self):
        """LIGHT_SENSOR_XP: Returns the light sensor in the x+ direction
        :return: object or None
        """
        return self._light_sensor_xp

    @property
    def LIGHT_SENSOR_XM(self):
        """LIGHT_SENSOR_XM: Returns the light sensor in the x- direction
        :return: object or None
        """
        return self._light_sensor_xm

    @property
    def LIGHT_SENSOR_YP(self):
        """LIGHT_SENSOR_YP: Returns the light sensor in the y+ direction
        :return: object or None
        """
        return self._light_sensor_yp

    @property
    def LIGHT_SENSOR_YM(self):
        """LIGHT_SENSOR_YM: Returns the light sensor in the y- direction
        :return: object or None
        """
        return self._light_sensor_ym

    @property
    def LIGHT_SENSOR_ZM(self):
        """LIGHT_SENSOR_ZM: Returns the light sensor in the z- direction
        :return: object or None
        """
        return self._light_sensor_zm

    @property
    def RTC(self):
        """RTC: Returns the RTC object
        :return: object or None
        """
        return self._rtc

    @property
    def RADIO(self):
        """RADIO: Returns the radio object
        :return: object or None
        """
        return self._radio

    @property
    def BURN_WIRES(self):
        """BURN_WIRES: Returns the burn wire object
        :return: object or None
        """
        return self._burn_wires

    @property
    def SD_CARD(self):
        """SD_CARD: Returns the SD card object
        :return: object or None
        """
        return self._sd_card

    @property
    def VFS(self):
        """VFS: Returns the VFS object
        :return: object or None
        """
        return self._vfs

    @property
    def PAYLOADUART(self):
        """PAYLOAD_EN: Returns the payload enable object
        :return: object or None
        """
        return self._payload_uart

    @property
    def BOOTTIME(self):
        """BOOTTIME: Returns the reference count since the board booted
        :return: object or None
        """
        return self._time_ref_boot
