import time

import supervisor
from hal.configuration import SATELLITE

print("Booting ARGUS...")
SATELLITE.boot_sequence()
print("ARGUS booted.")
print(f"Boot Errors: {SATELLITE.ERRORS}")

supervisor.runtime.autoreload = False

COILS = ["XP", "XM", "YP", "YM", "ZP", "ZM"]
N_STEPS = 60
STEP_SIZE = 2.0 / N_STEPS  # Map 0-255 to -1.0 to 1.0
STEPS = [round(-1.0 + i * STEP_SIZE, 2) for i in range(N_STEPS + 1)]  # -1.0 to 1.0 in steps
SETTLE_TIME = 0.2  # seconds to wait after setting throttle before sampling

headers = [
    "coil",
    "step",
    "time_ns",
    "mag_x",
    "mag_y",
    "mag_z",
    "voltage_xp",
    "voltage_xm",
    "voltage_yp",
    "voltage_ym",
    "voltage_zp",
    "voltage_zm",
    "current_xp",
    "current_xm",
    "current_yp",
    "current_ym",
    "current_zp",
    "current_zm",
]
print(",".join(headers))

for coil in COILS:
    SATELLITE.TORQUE_DRIVERS[coil].set_throttle(0)

for coil in COILS:
    for step in STEPS:
        for c in COILS:
            SATELLITE.TORQUE_DRIVERS[c].set_throttle(step if c == coil else 0)

        time.sleep(SETTLE_TIME)

        curr_time = int(1e9 * time.monotonic())
        mag = SATELLITE.IMU.mag()

        voltages = [SATELLITE.TORQUE_DRIVERS[c].__read_voltage() for c in COILS]
        currents = [SATELLITE.TORQUE_DRIVERS[c].__read_current() for c in COILS]

        row = [coil, step, curr_time] + list(mag) + voltages + currents
        print(",".join(map(str, row)))

for coil in COILS:
    SATELLITE.TORQUE_DRIVERS[coil].set_throttle(0)
