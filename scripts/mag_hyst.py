import circuitpython_csv as csv
import time
import supervisor
from hal.configuration import SATELLITE

print("Booting ARGUS-1...")
boot_errors = SATELLITE.boot_sequence()
print("ARGUS-1 booted.")
print(f"Boot Errors: {boot_errors}")
data = []

current_time = time.localtime()
date = SATELLITE.RTC.datetime
supervisor.runtime.autoreload = False

start_time = int(time.monotonic())
strengths = [1.0, 0.0, 0.75, 0.0, 0.5, 0.0, 0.25, 0.0]
idx = 0

while (idx < len(strengths)):

    curr_time = int(time.monotonic())

    SATELLITE.TORQUE_DRIVERS["YP"].set_throttle(strengths[idx])

    mag = SATELLITE.IMU.mag()

    applied_strength = SATELLITE.__torque_drivers["YP"].throttle()

    if (curr_time-start_time) > 20:
        idx += 1
        start_time = curr_time

    time.sleep(0.1)