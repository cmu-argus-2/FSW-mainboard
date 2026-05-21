"""
This module provides a custom accelerated time module for the emulator for testing purposes.

Author: Ibrahima S. Sow, Karthik Karumanchi

"""

import time as real_time

real_time_module = real_time


class MockTime:
    def __init__(self):
        self.__simulator = None
        self.acceleration = None  # set from simulator params via set_simulator(); None = full CPU speed
        self._sim_elapsed = 0.0
        self._epoch_offset = real_time.time()  # Unix epoch at sim start

    def set_simulator(self, simulator):
        self.__simulator = simulator
        self.acceleration = simulator.speedup  # None means full speed, number means X× real-time pacing

    def time(self):
        return self._epoch_offset + self._sim_elapsed

    def time_ns(self):
        return int((self._epoch_offset + self._sim_elapsed) * 1e9)

    def sleep(self, seconds):
        self._sim_elapsed += seconds
        if self.__simulator is not None:
            self.__simulator.advance_by_simtime(seconds)
        if self.acceleration is not None:
            real_time.sleep(seconds / self.acceleration)

    def monotonic(self):
        return self._sim_elapsed

    def monotonic_ns(self):
        return int(self._sim_elapsed * 1e9)

    def localtime(self, secs=None):
        return real_time.localtime(self.time() if secs is None else secs)

    def gmtime(self, secs=None):
        return real_time.gmtime(self.time() if secs is None else secs)

    def tzset(self):
        pass

    def debug(self):
        return "Mock Time Active"

    def __getattr__(self, name):
        return getattr(real_time, name)
