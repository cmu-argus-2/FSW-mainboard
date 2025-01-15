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
        self._board_power_monitor = None
        self._jetson_power_monitor = None
        self._imu = None
        self._imu_temp_flag = False
        self._charger = None
        self._torque_drivers = {}
        self._light_sensors = {}
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
    def GPS_AVAILABLE(self) -> bool:
        """GPS_AVAILABLE: Returns True if the GPS is available
        :return: bool
        """
        return self._gps is not None

    @property
    def BOARD_POWER_MONITOR(self):
        """BOARD_POWER_MONITOR: Returns the board power monitor object
        :return: object or None
        """
        return self._board_power_monitor

    @property
    def BOARD_POWER_MONITOR_AVAILABLE(self) -> bool:
        """BOARD_POWER_MONITOR_AVAILABLE: Returns True if the board power monitor is available
        :return: bool
        """
        return self._board_power_monitor is not None

    @property
    def JETSON_POWER_MONITOR(self):
        """JETSON_MONITOR: Returns the Jetson monitor object
        :return: object or None
        """
        return self._jetson_power_monitor

    @property
    def JETSON_POWER_MONITOR_AVAILABLE(self) -> bool:
        """JETSON_POWER_MONITOR_AVAILABLE: Returns True if the Jetson power monitor is available
        :return: bool
        """
        return self._jetson_power_monitor is not None

    @property
    def IMU(self):
        """IMU: Returns the IMU object
        :return: object or None
        """
        return self._imu

    @property
    def IMU_AVAILABLE(self) -> bool:
        """IMU_AVAILABLE: Returns True if the IMU is available
        :return: bool
        """
        return self._imu is not None

    @property
    def IMU_TEMPERATURE_AVAILABLE(self) -> bool:
        """IMU_AVAILABLE: Returns True if the IMU is available
        :return: bool
        """
        return self._imu_temp_flag

    @property
    def CHARGER(self):
        """CHARGER: Returns the charger object
        :return: object or None
        """
        return self._charger

    @property
    def CHARGER_AVAILABLE(self) -> bool:
        """CHARGER_AVAILABLE: Returns True if the charger is available
        :return: bool
        """
        return self._charger is not None

    @property
    def TORQUE_XP_POWER_MONITOR(self):
        """TORQUE_XP: Returns the torque driver in the x+ direction
        :return: object or None
        """
        return self._torque_xp_power_monitor

    @property
    def TORQUE_XP_POWER_MONITOR_AVAILABLE(self) -> bool:
        """TORQUE_XP_POWER_MONITOR_AVAILABLE: Returns True if the torque driver in the x+ direction is available
        :return: bool
        """
        return self._torque_xp_power_monitor is not None

    @property
    def TORQUE_DRIVERS(self):
        """Returns a dictionary of torque drivers with the direction as the key (e.g. 'XP', 'XM', 'YP', 'YM', 'ZM')"""
        return self._torque_drivers

    def TORQUE_DRIVERS_AVAILABLE(self, dir: str) -> bool:
        """Returns True if the specific torque driver for the given direction is available.

        :param dir: The direction key (e.g., 'XP', 'XM', etc.)
        :return: bool - True if the driver exists and is not None, False otherwise.
        """
        return self._torque_drivers.exist(dir) and self._torque_drivers[dir] is not None

    @property
    def LIGHT_SENSORS(self):
        """Returns a dictionary of light sensors with the direction as the key (e.g. 'XP', 'XM', 'YP', 'YM', 'ZM')"""
        return self._light_sensors

    def LIGHT_SENSOR_AVAILABLE(self, dir: str) -> bool:
        """Returns True if the specific light sensor for the given direction is available.

        :param dir: The direction key (e.g., 'XP', 'XM', etc.)
        :return: bool - True if the sensor exists and is not None, False otherwise.
        """
        return dir in self._light_sensors and self._light_sensors[dir] is not None

    @property
    def RTC(self):
        """RTC: Returns the RTC object
        :return: object or None
        """
        return self._rtc

    @property
    def RTC_AVAILABLE(self) -> bool:
        """RTC_AVAILABLE: Returns True if the RTC is available
        :return: bool
        """
        return self._rtc is not None

    @property
    def RADIO(self):
        """RADIO: Returns the radio object
        :return: object or None
        """
        return self._radio

    @property
    def RADIO_AVAILABLE(self) -> bool:
        """RADIO_AVAILABLE: Returns True if the radio is available
        :return: bool
        """
        return self._radio is not None

    @property
    def BURN_WIRES(self):
        """BURN_WIRES: Returns the burn wire object
        :return: object or None
        """
        return self._burn_wires

    @property
    def BURN_WIRES_AVAILABLE(self) -> bool:
        """BURN_WIRES_AVAILABLE: Returns True if the burn wires are available
        :return: bool
        """
        return self._burn_wires is not None

    @property
    def SD_CARD(self):
        """SD_CARD: Returns the SD card object
        :return: object or None
        """
        return self._sd_card

    @property
    def SD_CARD_AVAILABLE(self) -> bool:
        """SD_CARD_AVAILABLE: Returns True if the SD card is available
        :return: bool
        """
        return self._sd_card is not None

    @property
    def VFS(self):
        """VFS: Returns the VFS object
        :return: object or None
        """
        return self._vfs

    @property
    def VFS_AVAILABLE(self) -> bool:
        """VFS_AVAILABLE: Returns True if the VFS is available
        :return: bool
        """
        return self._vfs is not None

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
