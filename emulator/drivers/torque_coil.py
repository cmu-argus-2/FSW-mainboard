class CoilDriver:
    def __init__(self, id, simulator=None) -> None:
        self.__simulator = simulator
        self.__id = id
        self.current_throttle = 0
        self.current_throttle_volts = 0
        self.__voltage = 0
        self.__current = 0

    def set_throttle_volts(self, new_throttle_volts):
        self.current_throttle_volts = new_throttle_volts

    def set_throttle(self, dir, ctrl):
        self.current_throttle = ctrl
        if self.__simulator is not None:
            self.__simulator.set_control_input(dir, ctrl)

    def read_voltage_current(self):
        if self.__simulator is not None:
            self.__voltage = self.current_throttle * 5
            self.__current = (self.__simulator.coil_power(self.__id) / self.__voltage) if self.__voltage != 0 else 0

        return (self.__voltage, self.__current)


class TorqueCoilArray:
    def __init__(self, simulator=None) -> None:
        # failure injection
        torque_status = [True for _ in range(6)]
        if simulator is not None:
            torque_status = simulator.cppsim.params.mtb_working_status
        self.torque_coils = {
            "XP": CoilDriver(0, simulator) if torque_status[0] else None,
            "XM": CoilDriver(1, simulator) if torque_status[1] else None,
            "YP": CoilDriver(2, simulator) if torque_status[2] else None,
            "YM": CoilDriver(3, simulator) if torque_status[3] else None,
            "ZP": CoilDriver(4, simulator) if torque_status[4] else None,
            "ZM": CoilDriver(5, simulator) if torque_status[5] else None,
        }
        self.__simulator = simulator

    def __getitem__(self, face: str):
        return self.torque_coils.get(face, None)

    def exist(self, face: str):
        return face in self.torque_coils

    def apply_control(self, dir, ctrl):
        if self.__simulator is not None:
            self.__simulator.set_control_input(dir, ctrl)
