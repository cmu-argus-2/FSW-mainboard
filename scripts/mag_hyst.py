import time

# import circuitpython_csv as csv
import supervisor
from hal.configuration import SATELLITE

print("Booting ARGUS...")
SATELLITE.boot_sequence()
print("ARGUS booted.")
print(f"Boot Errors: {SATELLITE.ERRORS}")

supervisor.runtime.autoreload = False

# File Structure
filename = "/sd/magneto_data.txt"
file_headers = [
    "Time (ns)",
    "Coil Strength XP",
    "Coil Strength XM",
    "Coil Strength YP",
    "Coil Strength YM",
    "Voltage XP",
    "Voltage XM",
    "Voltage YP",
    "Voltage YM",
    "Current XP",
    "Current XM",
    "Current YP",
    "Current YM",
    "MAG_X",
    "MAG_Y",
    "MAG_Z",
]
with open(filename, "w") as file:
    file.write(",".join(file_headers) + "\n")

# Logging Details
data = []
last_update_time = 0
UPDATE_PERIOD = 5e9  # 5s

# Test Configuration
start_time = int(1e9 * time.monotonic())
active_strengths = [1 - 0.05 * i for i in range(20)]
strengths = []
for i in range(len(active_strengths)):
    strengths.append(active_strengths[i])
    strengths.append(0)
idx = -1
SWITCH_PERIOD = 7e9

# Satellite Confn
torquer_dirs = ["XP", "XM", "YP", "YM"]
N_dirs = len(torquer_dirs)
active_dir_idx = 0
for dir in torquer_dirs:
    SATELLITE.TORQUE_DRIVERS[dir].set_throttle(0)


def flush_to_sd_card(data):

    with open(filename, "a") as file:
        for row in data:
            file.write(",".join(map(str, row)) + "\n")
    print("Data flushed to SD card.")


while idx < len(strengths):

    curr_time = int(1e9 * time.monotonic())

    mag = SATELLITE.IMU.mag()

    strength_xp = SATELLITE.TORQUE_DRIVERS["XP"].throttle()
    strength_xm = SATELLITE.TORQUE_DRIVERS["XM"].throttle()
    strength_yp = SATELLITE.TORQUE_DRIVERS["YP"].throttle()
    strength_ym = SATELLITE.TORQUE_DRIVERS["YM"].throttle()

    voltage_xp = SATELLITE.TORQUE_DRIVERS["XP"].read_voltage()
    voltage_xm = SATELLITE.TORQUE_DRIVERS["XM"].read_voltage()
    voltage_yp = SATELLITE.TORQUE_DRIVERS["YP"].read_voltage()
    voltage_ym = SATELLITE.TORQUE_DRIVERS["YM"].read_voltage()

    current_xp = SATELLITE.TORQUE_DRIVERS["XP"].read_current()
    current_xm = SATELLITE.TORQUE_DRIVERS["XM"].read_current()
    current_yp = SATELLITE.TORQUE_DRIVERS["YP"].read_current()
    current_ym = SATELLITE.TORQUE_DRIVERS["YM"].read_current()

    data.append([curr_time, strength_xp, strength_xm, strength_yp, strength_ym, voltage_xp, voltage_xm, voltage_yp, voltage_ym, current_xp, current_xm, current_yp, current_ym] + list(mag))

    if (curr_time - start_time) > SWITCH_PERIOD:
        print(f"Done with strength {strengths[idx]}")
        idx += 1
        start_time = curr_time

        # Switch active dir
        active_dir_idx += 1
        if active_dir_idx >= N_dirs:
            active_dir_idx = 0

        for i in range(N_dirs):
            if i == active_dir_idx:
                SATELLITE.TORQUE_DRIVERS[torquer_dirs[i]].set_throttle(strengths[idx])
            else:
                SATELLITE.TORQUE_DRIVERS[torquer_dirs[i]].set_throttle(0)

    if (curr_time - last_update_time) > UPDATE_PERIOD:
        flush_to_sd_card(data)
        data.clear()
        last_update_time = curr_time

    time.sleep(0.001)
