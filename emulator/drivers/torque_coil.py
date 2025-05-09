from hal.drivers.errors import Errors
from hal.drivers.failure_prob import torque_coil_prob
from ulab import numpy as np

_scale_ = torque_coil_prob.scale


class CoilDriver:
    def __init__(self, id, simulator=None) -> None:
        self.__simulator = simulator
        self.__id = id
        self.current_throttle = 0
        self.__voltage = 0
        self.__current = 0

        # Faults
        self._fault = False
        self._all_faults = np.array([False] * 5)
        self._time_to_each_failure = np.random.exponential(scale=_scale_)

        self._stall = False
        self._ocp = False
        self._ovp = False
        self._tsd = False
        self._npor = False

    def set_throttle_volts(self, new_throttle_volts):
        self.current_throttle = new_throttle_volts

    def set_throttle(self, dir, ctrl):
        if self.__simulator is not None:
            self.simulate_fault()
            if not self._fault:
                self.__simulator.set_control_input(dir, ctrl)

    def read_voltage_current(self):
        return (self.__voltage, self.__current)

    ######################## ERROR HANDLING ########################

    def simulate_fault(self):
        time_since_boot = self.__simulator.sim_time
        self._all_faults = self._time_to_each_failure < time_since_boot

        if np.any(self._all_faults):
            self._fault = True

        self._stall, self._ocp, self._ovp, self._tsd, self._npor = self._all_faults

    def clear_faults(self):
        self._fault = False

        # If simulator is available, update new times for faults to show up
        if self.__simulator is not None:
            self._time_to_each_failure = (
                self._time_to_each_failure * (1 - self._all_faults)
                + (self.__simulator.sim_time + np.random.exponential(scale=_scale_)) * self._all_faults
            )
        self._all_faults = self._all_faults & False
        self._stall, self._ocp, self._ovp, self._tsd, self._npor = self._all_faults

    @property
    def device_errors(self):

        results = []
        if self._fault:
            if self._stall:
                results.append(Errors.TORQUE_COIL_STALL_EVENT)
            if self._ocp:
                results.append(Errors.TORQUE_COIL_OVERCURRENT_EVENT)
            if self._ovp:
                results.append(Errors.TORQUE_COIL_OVERVOLTAGE_EVENT)
            if self._tsd:
                results.append(Errors.TORQUE_COIL_THERMAL_SHUTDOWN)
            if self._npor:
                results.append(Errors.TORQUE_COIL_UNDERVOLTAGE_LOCKOUT)
            self.clear_faults()
        return results

    def deinit(self):
        return


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
