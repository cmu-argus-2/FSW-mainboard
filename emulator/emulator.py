import time
from typing import List, Optional

from hal.cubesat import CubeSat
from hal.drivers.burnwire import BurnWires
from hal.drivers.fuel_gauge import FuelGauge
from hal.drivers.gps import GPS
from hal.drivers.imu import IMU
from hal.drivers.payload import Payload
from hal.drivers.power_monitor import PowerMonitor
from hal.drivers.radio import Radio
from hal.drivers.rtc import RTC
from hal.drivers.sd import SD
from hal.drivers.sun_sensor import LightSensor
from hal.drivers.torque_coil import CoilDriver


class device:
    """
    Based on the code from: https://docs.python.org/3/howto/descriptor.html#properties
    Attempts to return the appropriate hardware device.
    If this fails, it will attempt to reinitialize the hardware.
    If this fails again, it will raise an exception.
    """

    def __init__(self, fget=None):
        self.fget = fget
        self._device = None

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        if self.fget is None:
            raise AttributeError(f"unreadable attribute {self._name}")

        if self._device is not None:
            return self._device
        else:
            self._device = self.fget(instance)
            return self._device


class EmulatedSatellite(CubeSat):
    def __init__(self, debug: bool, simulator, use_socket) -> None:
        self.__debug = debug
        self.__use_socket = use_socket
        self.__simulated_spacecraft = simulator

        super().__init__()

        self._device_list["RADIO"].device = Radio(self.__use_socket)
        self._device_list["SDCARD"].device = SD()
        self._device_list["BURN_WIRE"].device = self.init_device(BurnWires())
        self._payload_uart = self.init_device(Payload())

        # self._vfs = None
        self._device_list["GPS"].device = self.init_device(GPS(simulator=self.__simulated_spacecraft))
        # self._charger = None

        self._device_list["LIGHT_XP"].device = self.init_device(LightSensor(4500, 0, simulator=self.__simulated_spacecraft))
        self._device_list["LIGHT_XM"].device = self.init_device(LightSensor(48000, 1, simulator=self.__simulated_spacecraft))
        self._device_list["LIGHT_YP"].device = self.init_device(LightSensor(85000, 2, simulator=self.__simulated_spacecraft))
        self._device_list["LIGHT_YM"].device = self.init_device(LightSensor(0, 3, simulator=self.__simulated_spacecraft))
        self._device_list["LIGHT_ZM"].device = self.init_device(LightSensor(0, 4, simulator=self.__simulated_spacecraft))

        # self._torque_drivers = TorqueCoilArray(simulator=self.__simulated_spacecraft)
        self._device_list["TORQUE_XP"].device = self.init_device(CoilDriver(0, simulator=self.__simulated_spacecraft))
        self._device_list["TORQUE_XM"].device = self.init_device(CoilDriver(1, simulator=self.__simulated_spacecraft))
        self._device_list["TORQUE_YP"].device = self.init_device(CoilDriver(2, simulator=self.__simulated_spacecraft))
        self._device_list["TORQUE_YM"].device = self.init_device(CoilDriver(3, simulator=self.__simulated_spacecraft))
        self._device_list["TORQUE_ZP"].device = self.init_device(CoilDriver(4, simulator=self.__simulated_spacecraft))
        self._device_list["TORQUE_ZM"].device = self.init_device(CoilDriver(5, simulator=self.__simulated_spacecraft))

        self._device_list["IMU"].device = self.init_device(IMU(simulator=self.__simulated_spacecraft))
        self._device_list["IMU"].device.enable()

        self._device_list["BOARD_PWR"].device = self.init_device(PowerMonitor(7.6, 0.1))
        self._device_list["JETSON_PWR"].device = self.init_device(PowerMonitor(4, 0.05))

        self._device_list["FUEL_GAUGE"].device = self.init_device(FuelGauge())

        self._device_list["RTC"].device = self.init_device(RTC(time.gmtime()))

    def init_device(self, device):
        return device

    def boot_sequence(self) -> List[int]:
        pass

    def run_system_diagnostics(self) -> Optional[List[int]]:
        pass

    ######################## INTERFACES ########################
    def APPLY_MAGNETIC_CONTROL(self, dir, ctrl) -> None:
        """CONTROL_COILS: Control the coils on the CubeSat, depending on the control mode (identical for all coils)."""
        self._torque_drivers.apply_control(dir, ctrl)
