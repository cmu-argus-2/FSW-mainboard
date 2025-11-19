import time
from typing import List, Optional

from hal.cubesat import CubeSat
from hal.drivers.burnwire import BurnWires
from hal.drivers.deployment_sensor import DeploymentSensor
from hal.drivers.errors import Errors
from hal.drivers.fuel_gauge import FuelGauge
from hal.drivers.gps import GPS
from hal.drivers.imu import IMU
from hal.drivers.payload import Payload
from hal.drivers.power_monitor import PowerMonitor
from hal.drivers.radio import Radio
from hal.drivers.rtc import RTC
from hal.drivers.sd import SD
from hal.drivers.sun_sensor import LightSensor
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

        # self._radio = Radio(self.__use_socket)
        self.append_device("RADIO", None, Radio(self.__use_socket), ASIL=4)
        # self._sd_card = SD()
        self.append_device("SDCARD", None, SD(), ASIL=1)
        # self._burnwires = self.init_device(BurnWires())
        self.append_device("BURN_WIRES", None, BurnWires(), ASIL=4)

        self.append_device("PAYLOAD_UART", None, self.init_device(Payload()))

        # self._vfs = None
        self.append_device("GPS", None, GPS(simulator=self.__simulated_spacecraft))
        # self._charger = None

        self.append_device("LIGHT_XP", None, LightSensor("XP", simulator=self.__simulated_spacecraft), ASIL=2)
        self.append_device("LIGHT_XM", None, LightSensor("XM", simulator=self.__simulated_spacecraft), ASIL=2)
        self.append_device("LIGHT_YP", None, LightSensor("YP", simulator=self.__simulated_spacecraft), ASIL=2)
        self.append_device("LIGHT_YM", None, LightSensor("YM", simulator=self.__simulated_spacecraft), ASIL=2)
        self.append_device("LIGHT_ZP1", None, LightSensor("ZP1", simulator=self.__simulated_spacecraft), ASIL=2)
        self.append_device("LIGHT_ZP2", None, LightSensor("ZP2", simulator=self.__simulated_spacecraft), ASIL=2)
        self.append_device("LIGHT_ZP3", None, LightSensor("ZP3", simulator=self.__simulated_spacecraft), ASIL=2)
        self.append_device("LIGHT_ZP4", None, LightSensor("ZP4", simulator=self.__simulated_spacecraft), ASIL=2)
        self.append_device("LIGHT_ZM", None, LightSensor("ZM", simulator=self.__simulated_spacecraft), ASIL=2)

        self._torque_drivers = TorqueCoilArray(simulator=self.__simulated_spacecraft)
        self.append_device("TORQUE_XP", None, self._torque_drivers["XP"], ASIL=3)
        self.append_device("TORQUE_XM", None, self._torque_drivers["XM"], ASIL=3)
        self.append_device("TORQUE_YP", None, self._torque_drivers["YP"], ASIL=3)
        self.append_device("TORQUE_YM", None, self._torque_drivers["YM"], ASIL=3)
        self.append_device("TORQUE_ZP", None, self._torque_drivers["ZP"], ASIL=3)
        self.append_device("TORQUE_ZM", None, self._torque_drivers["ZM"], ASIL=3)

        self._imu = self.init_device(IMU(simulator=self.__simulated_spacecraft))
        self._imu.enable()
        self.append_device("IMU", None, self._imu, ASIL=3)
        # Board Power monitor
        self.append_device("BOARD_PWR", None, PowerMonitor(device_name="BOARD", voltage=7.6, current=0.1), ASIL=1)

        # Solar Power monitors
        self.append_device("XP_PWR", None, PowerMonitor(device_name="XP", simulator=self.__simulated_spacecraft), ASIL=1)
        self.append_device("XM_PWR", None, PowerMonitor(device_name="XM", simulator=self.__simulated_spacecraft), ASIL=1)
        self.append_device("YP_PWR", None, PowerMonitor(device_name="YP", simulator=self.__simulated_spacecraft), ASIL=1)
        self.append_device("YM_PWR", None, PowerMonitor(device_name="YM", simulator=self.__simulated_spacecraft), ASIL=1)
        self.append_device("ZP_PWR", None, PowerMonitor(device_name="ZP", simulator=self.__simulated_spacecraft), ASIL=1)

        # Jetson Power Monitor
        self.append_device("JETSON_PWR", None, PowerMonitor("JETSON", simulator=self.__simulated_spacecraft), ASIL=1)

        # Fuel Gauge
        self.append_device("FUEL_GAUGE", None, FuelGauge(simulator=self.__simulated_spacecraft), ASIL=2)

        # RTC
        self.append_device("RTC", None, RTC(time.gmtime(), simulator=self.__simulated_spacecraft), ASIL=2)

        # Deployment Sensors
        self.append_device("DEPLOYMENT_XP", None, DeploymentSensor("XP", simulator=self.__simulated_spacecraft))
        self.append_device("DEPLOYMENT_YM", None, DeploymentSensor("YM", simulator=self.__simulated_spacecraft))

        # self.ERRORS = []

    def init_device(self, device):
        return device

    def boot_sequence(self) -> List[int]:
        pass

    def run_system_diagnostics(self) -> Optional[List[int]]:
        pass

    ######################## INTERFACES ########################
    def APPLY_MAGNETIC_CONTROL(self, dir, ctrl) -> None:
        """CONTROL_COILS: Control the coils on the CubeSat, depending on the control mode (identical for all coils)."""
        # self._torque_drivers.apply_control(dir, ctrl)
        if self.TORQUE_DRIVERS_AVAILABLE(dir):
            if ctrl != ctrl:
                print(f"[WARNING] [6][ADCS] Trying to set a NaN input to {dir} coil")
                return
            self.DEVICE_LIST["TORQUE_" + dir].device.set_throttle(dir, ctrl)

    def set_fsw_state(self, state):
        self.__simulated_spacecraft.set_fsw_state(state)

    ######################## ERROR HANDLING ########################

    def handle_error(self, _: str) -> int:
        return Errors.NO_REBOOT

    def graceful_reboot_devices(self, device_name):
        pass

    def reboot(self):
        pass
