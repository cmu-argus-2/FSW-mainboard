from hal.drivers.errors import Errors
from ulab import numpy as np

# Failure Probabilities:
_prob_ = 2 * np.ones((3,))  # % of devices that throw [flag_h, flag_l, overload] fault in a day

_scale_ = -86400 / (np.log(1 - (0.01 * _prob_)))  # exponential distribution scale


class LightSensor:
    def __init__(self, lux, id, simulator=None) -> None:
        self.__simulator = simulator
        self.__lux = lux
        self.__id = id

        # Faults
        self._all_faults = np.array([False] * 3)
        self._time_to_each_failure = np.random.exponential(scale=_scale_)

        self.flag_h = False
        self.flag_L = False
        self.overload_flag = False

    def lux(self):
        if self.__simulator is not None:
            self.simulate_fault()
            return self.__simulator.sun_lux()[self.__id]
        return self.__lux

    ######################## ERROR HANDLING ########################
    def simulate_fault(self):
        time_since_boot = self.__simulator.sim_time
        self._all_faults = self._time_to_each_failure < time_since_boot

        self.flag_h, self.flag_L, self._overload_flag = self._all_faults

    def clear_faults(self):

        # If simulator is available, update new times for faults to show up
        if self.__simulator is not None:
            self._time_to_each_failure = (
                self._time_to_each_failure * (1 - self._all_faults)
                + (self.__simulator.sim_time + np.random.exponential(scale=_scale_)) * self._all_faults
            )

        self._all_faults = self._all_faults & False
        self.flag_h, self.flag_L, self._overload_flag = self._all_faults

    @property
    def device_errors(self):
        if self.__simulator is not None:
            self.simulate_fault()

        results = []
        if self.flag_h:
            results.append(Errors.LIGHT_SENSOR_HIGHER_THAN_THRESHOLD)
        if self.flag_L:
            results.append(Errors.LIGHT_SENSOR_LOWER_THAN_THRESHOLD)
        if self.overload_flag:
            results.append(Errors.LIGHT_SENSOR_OVERFLOW)

        self.clear_faults()
        return results

    def deinit(self):
        return


class LightSensorArray:
    def __init__(self, simulator=None) -> None:
        self.light_sensors = {
            "XP": LightSensor(4500, 0, simulator),
            "XM": LightSensor(48000, 1, simulator),
            "YP": LightSensor(85000, 2, simulator),
            "YM": LightSensor(0, 3, simulator),
            "ZM": LightSensor(0, 4, simulator),
        }

    def __getitem__(self, face):
        return self.light_sensors.get(face, None)
