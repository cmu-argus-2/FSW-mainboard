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
from hal.drivers.sun_sensor import LightSensorArray
from hal.drivers.torque_coil import TorqueCoilArray


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

        self._radio = Radio(self.__use_socket)
        self._sd_card = SD()
        self._burnwires = self.init_device(BurnWires())
        self._payload_uart = self.init_device(Payload())

        self._vfs = None
        self._gps = self.init_device(GPS(simulator=self.__simulated_spacecraft))
        self._charger = None

        self._light_sensors = LightSensorArray(simulator=self.__simulated_spacecraft)

        self._torque_drivers = TorqueCoilArray(simulator=self.__simulated_spacecraft)

        self._imu = self.init_device(IMU(simulator=self.__simulated_spacecraft))
        self._imu.enable()

        self._jetson_power_monitor = self.init_device(PowerMonitor(4, 0.05))
        self._board_power_monitor = self.init_device(PowerMonitor(7.6, 0.1))
        self._power_monitors["BOARD"] = self._board_power_monitor
        self._power_monitors["JETSON"] = self._jetson_power_monitor

        self._fuel_gauge = self.init_device(FuelGauge())

        self._rtc = self.init_device(RTC(time.gmtime()))

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
