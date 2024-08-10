import time
from typing import List, Optional

from hal.cubesat import CubeSat
from hal.drivers.burnwire import BurnWires
from hal.drivers.imu import IMU
from hal.drivers.light_sensor import LightSensor
from hal.drivers.middleware.generic_driver import Driver
from hal.drivers.middleware.middleware import Middleware
from hal.drivers.payload import Payload
from hal.drivers.power_monitor import PowerMonitor
from hal.drivers.radio import Radio
from hal.drivers.rtc import RTC
from hal.drivers.sd import SD
from numpy import array


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


class satellite(CubeSat):
    def __init__(self, enable_middleware, debug, use_socket) -> None:
        self.__middleware_enabled = enable_middleware
        self.__debug = debug
        self.__use_socket = use_socket

        super().__init__()

        self._radio = Radio(self.__use_socket)
        self._sd_card = SD()
        self._burnwires = self.init_device(BurnWires())
        self._payload_uart = self.init_device(Payload())

        self._vfs = None
        self._gps = None
        self._charger = None

        self._light_sensor_xp = self.init_device(LightSensor(900))
        self._light_sensor_xm = self.init_device(LightSensor(48000))
        self._light_sensor_yp = self.init_device(LightSensor(85000))
        self._light_sensor_ym = self.init_device(LightSensor(200))
        self._light_sensor_zm = self.init_device(LightSensor(12000))

        self._torque_x = None
        self._torque_y = None
        self._torque_z = None

        accel = array([1.0, 2.0, 3.0])
        mag = array([4.0, 3.0, 1.0])
        gyro = array([0.0, 0.0, 0.0])
        self._imu = self.init_device(IMU(accel=accel, mag=mag, gyro=gyro, temp=20))
        self._imu.enable()

        self._jetson_monitor = self.init_device(PowerMonitor(4, 0.05))
        self._battery_monitor = self.init_device(PowerMonitor(7.6, 0.1))

        self._rtc = self.init_device(RTC(time.gmtime()))

    def init_device(self, device) -> Driver:
        if self.__middleware_enabled:
            return Middleware(device)
        return device

    def boot_sequence(self) -> List[int]:
        pass

    def run_system_diagnostics(self) -> Optional[List[int]]:
        pass
