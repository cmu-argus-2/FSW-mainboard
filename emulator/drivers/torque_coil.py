class CoilDriver:
    def __init__(self, id, simulator=None) -> None:
        self.__simulator = simulator
        self.__id = id
        self.current_throttle = 0

    def set_throttle_volts(self, new_throttle_volts):
        self.current_throttle = new_throttle_volts


class TorqueCoilArray:
    def __init__(self, simulator=None) -> None:
        self.torque_coils = {
            "XP": CoilDriver(0, simulator),
            "XM": CoilDriver(1, simulator),
            "YP": CoilDriver(2, simulator),
            "YM": CoilDriver(3, simulator),
            "ZP": CoilDriver(4, simulator),
            "ZM": CoilDriver(5, simulator),
        }
        self.__simulator = simulator

    def __getitem__(self, face: str):
        return self.torque_coils.get(face, None)

    def exist(self, face: str):
        return face in self.torque_coils

    def apply_control(self, dir, ctrl):
        if self.__simulator is not None:
            self.__simulator.set_control_input(dir, ctrl)
