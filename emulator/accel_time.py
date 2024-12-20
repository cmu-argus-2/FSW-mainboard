"""
This module provides a custom accelerated time module for the emulator for testing purposes.

Author: Ibrahima S. Sow

"""

import sys
import time as real_time

real_time_module = real_time


class MockTime:
    def __init__(self, acceleration=1.0):
        self.acceleration = acceleration
        self.start_real_time = real_time.time()
        self.start_real_time_monotonic = real_time.monotonic()
        self.start_simulated_time = real_time.time()

    def time(self):
        real_elapsed = real_time.time() - self.start_real_time
        return self.start_simulated_time + real_elapsed * self.acceleration

    def sleep(self, seconds):
        real_time.sleep(seconds / self.acceleration)

    def localtime(self, secs=None):
        simulated_secs = self.time() if secs is None else secs
        return real_time.localtime(simulated_secs)

    def monotonic(self):
        real_elapsed = real_time.monotonic() - self.start_real_time_monotonic
        return real_elapsed * self.acceleration

    def tzset(self):
        pass


# Context manager for temporarily replacing the time module
class ScopedTimeMock:
    def __init__(self, mock_time_module):
        self.mock_time_module = mock_time_module
        self.original_time_module = sys.modules.get("time")

    def __enter__(self):
        sys.modules["time"] = self.mock_time_module

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.modules["time"] = self.original_time_module


# Instantiate the mock time
mock_time = MockTime(acceleration=100)


# Replace in sys.modules
class TimeMockModule:
    def __getattr__(self, name):
        if name == "time":
            return mock_time.time
        if name == "sleep":
            return mock_time.sleep
        if name == "localtime":
            return mock_time.localtime
        if name == "monotonic":
            return mock_time.monotonic
        if name == "tzset":
            return mock_time.tzset
        # Forward any other attributes to the real time module
        return getattr(real_time, name)


# sys.modules["time"] = TimeMockModule()


if __name__ == "__main__":
    import time

    print("Simulated start time:", time.time())
    print("Simulated local time:", time.localtime())
    time.sleep(10)
    print("Simulated end time:", time.time())
    print("Simulated monotonic time:", time.monotonic())
