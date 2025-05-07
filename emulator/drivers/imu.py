from hal.drivers.errors import Errors
from numpy import array
from ulab import numpy as np

# Failure Probabilities:
_prob_ = np.array([2, 0.1])  # % of devices that throw [drop_cmd, fatal_err] fault in a day

_scale_ = -86400 / (np.log(1 - (0.01 * _prob_)))  # exponential distribution scale

BMX160_OK = 0


class IMU:
    def __init__(self, simulator=None) -> None:
        self.__simulator = simulator

        self.__mag = array([4.0, 3.0, 1.0])
        self.__gyro = array([0.0, 0.0, 0.0])
        self.__temp = 20
        self.__enable = False

        self.__accel = array([0.0, 0.0, 0.0])

        # Faults
        self._all_faults = np.array([False] * 2)
        self._time_to_each_failure = np.random.exponential(scale=_scale_)

        self.drop_cmd_err = False
        self.fatal_err = False

    def accel(self):
        return self.__accel if self.__enable else None

    def mag(self):
        if self.__simulator:
            self.simulate_faults()
            return self.__simulator.mag()
        return self.__mag if self.__enable else None

    def gyro(self):
        if self.__simulator:
            self.simulate_faults()
            return self.__simulator.gyro()
        return self.__gyro if self.__enable else None

    def temperature(self):
        return self.__temp if self.__enable else None

    def enable(self):
        self.__enable = True

    def disable(self):
        self.__enable = False

    ######################## ERROR HANDLING ########################
    def simulate_faults(self):
        if self.fatal_err:
            return

        time_since_boot = self.__simulator.sim_time
        self._all_faults = self._time_to_each_failure < time_since_boot

        self.drop_cmd_err, self.fatal_err = self._all_faults

    def clear_faults(self):

        # If simulator is available, update new times for faults to show up
        if self.__simulator is not None:
            self._time_to_each_failure = (
                self._time_to_each_failure * (1 - self._all_faults)
                + (self.__simulator.sim_time + np.random.exponential(scale=_scale_)) * self._all_faults
            )

        self._all_faults[0:1] = self._all_faults[0:1] & False
        self.drop_cmd_err, self.fatal_err = self._all_faults

    @property
    def device_errors(self):
        results = []
        if self.drop_cmd_err:
            results.append(Errors.IMU_DROP_COMMAND_ERROR)
        if self.fatal_err:
            results.append(Errors.IMU_FATAL_ERROR)

        self.clear_faults()
        return results

    def deinit(self):
        return
