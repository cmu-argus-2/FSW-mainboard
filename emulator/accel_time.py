"""
This module provides a custom accelerated time module for the emulator for testing purposes.

Author: Ibrahima S. Sow

"""

import os
import sys
import time as real_time

real_time_module = real_time


class MockTime:
    def __init__(self):
        self.acceleration = int(os.environ["SIM_REAL_SPEEDUP"])

        # Datum references for Speedup
        self.start_real_time = real_time.time_ns() / 1.0e9
        self.start_real_time_monotonic = real_time.monotonic_ns() / 1.0e9

        # Spedup times
        self.spedup_time = self.start_real_time

        self.start_simulated_time = real_time.time()

    def time(self):
        real_elapsed = real_time.time_ns() / 1.0e9 - self.start_real_time
        self.spedup_time = self.start_real_time + real_elapsed * self.acceleration
        return self.spedup_time

    def sleep(self, seconds):
        real_time.sleep(seconds / self.acceleration)

    def localtime(self, secs=None):
        simulated_secs = self.time() if secs is None else secs
        return real_time.localtime(simulated_secs)

    def monotonic(self):
        real_elapsed = real_time.monotonic_ns() / 1.0e9 - self.start_real_time_monotonic
        return real_elapsed * self.acceleration

    def tzset(self):
        pass

    def gmtime(self, secs=None):
        simulated_secs = self.time() if secs is None else secs
        return real_time.gmtime(simulated_secs)

    def debug(self):
        return "Mock Time Active"

    def __getattr__(self, name):
        if name == "time":
            return self.time
        if name == "sleep":
            return self.sleep
        if name == "localtime":
            return self.localtime
        if name == "monotonic":
            return self.monotonic
        if name == "gmtime":
            return self.gmtime
        if name == "tzset":
            return self.tzset
        if name == "debug":
            return self.debug
        else:
            return getattr(real_time, name)
