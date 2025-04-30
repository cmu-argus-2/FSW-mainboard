from time import gmtime, monotonic, struct_time

from hal.drivers.errors import Errors
from ulab import numpy as np

# Failure Probabilities:
_prob_ = 2 * np.ones((2,))  # % of devices that throw [lost_power, battery_low] fault in a day

_scale_ = -86400 / (np.log(1 - (0.01 * _prob_)))  # exponential distribution scale


class RTC:
    def __init__(self, date_input: struct_time) -> None:
        self.current_datetime = date_input

        # faults
        self.start_time = monotonic()
        self._all_faults = np.array([False] * 2)
        self._time_to_each_failure = np.random.exponential(scale=_scale_)

        self.lost_power = False
        self.battery_low = False

    @property
    def datetime(self):
        self.current_datetime = gmtime()
        return self.current_datetime

    def set_datetime(self, date_input: struct_time):
        self.datetime = date_input

    ######################## ERROR HANDLING ########################
    def simulate_faults(self):
        time_since_boot = monotonic() - self.start_time
        self._all_faults = self._time_to_each_failure < time_since_boot

        self.lost_power, self.battery_low = self._all_faults

    def clear_faults(self):
        self._time_to_each_failure = (
            self._time_to_each_failure * (1 - self._all_faults)
            + (monotonic() - self.start_time + np.random.exponential(scale=_scale_)) * self._all_faults
        )

        self._all_faults = self._all_faults & False
        self.lost_power, self.battery_low = self._all_faults

    @property
    def device_errors(self):
        self.simulate_faults()

        results = []
        if self.lost_power:
            results.append(Errors.RTC_LOST_POWER)
        if self.battery_low:
            results.append(Errors.RTC_BATTERY_LOW)

        self.clear_faults()
        return results

    def deinit(self):
        return
