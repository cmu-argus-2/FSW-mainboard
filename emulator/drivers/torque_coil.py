import numpy as np
from hal.drivers.middleware.generic_driver import Driver


class CoilDriver(Driver):
    def __init__(self, id, simulator=None) -> None:
        self.__simulator = simulator
        self.__id = id
        self.current_throttle = 0
        super().__init__(None)

    def set_throttle_volts(self, new_throttle_volts):
        self.current_throttle = new_throttle_volts

    def run_diagnostics(self):
        return []

    def get_flags(self) -> dict:
        return {}


class TorqueCoilArray:
    def __init__(self, simulator=None) -> None:
        self.torque_coils = {
            "XP": CoilDriver(0, simulator),
            "XM": CoilDriver(1, simulator),
            "YP": CoilDriver(2, simulator),
            "YM": CoilDriver(3, simulator),
            "ZM": CoilDriver(4, simulator),
        }
        self.__simulator = simulator

    def __getitem__(self, face):
        return self.torque_coils.get(face, None)

    def apply_control(self, ctrl):
        if self.__simulator is not None:
            moment = np.zeros(3)
            # volts to moment

            # In X:
            moment[0] += self.__simulator.set_coil_throttle("XP", ctrl["XP"])
            moment[0] += self.__simulator.set_coil_throttle("XM", ctrl["XM"])
            # In Y:
            moment[1] += self.__simulator.set_coil_throttle("YP", ctrl["YP"])
            moment[1] += self.__simulator.set_coil_throttle("YM", ctrl["YM"])
            # In Z:
            moment[2] += self.__simulator.set_coil_throttle("ZP", ctrl["ZP"])
            moment[2] += self.__simulator.set_coil_throttle("ZM", ctrl["ZM"])

            self.__simulator.set_torque_to_spacecraft(moment)
