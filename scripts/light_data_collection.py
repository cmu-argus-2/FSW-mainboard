import time

import supervisor
from apps.adcs.sun import read_light_sensors
from hal.configuration import SATELLITE

print("Booting ARGUS...")
SATELLITE.boot_sequence()
print("ARGUS booted.")
print(f"Boot Errors: {SATELLITE.ERRORS}")
light_data = []

last_flush_time = time.monotonic()
current_time = time.localtime()
date = SATELLITE.RTC.datetime
formatted_time = f"{date.tm_year}-{date.tm_mon:02d}-{date.tm_mday:02d}_{date.tm_hour:02d}-{date.tm_min:02d}-{date.tm_sec:02d}"
supervisor.runtime.autoreload = False
filepath = f"/sd/light_data_{formatted_time}.txt"


def flush_to_sd_card():
    global light_data
    global filepath

    with open(filepath, "a") as file:
        for row in light_data:
            file.write(",".join(map(str, row)) + "\n")

    # Clear the data after flushing
    light_data.clear()
    print("Data flushed to SD card.")


def log_data(light_values):
    global last_flush_time
    global light_data

    current_time_ns = int(time.monotonic() * 1e9)
    light_data.append([current_time_ns] + light_values)

    if time.monotonic() - last_flush_time >= 30:
        flush_to_sd_card()
        last_flush_time = time.monotonic()


light_header = ["timestamp_ns"] + ["XP", "XM", "YP", "YM", "ZM"]

with open(filepath, "a") as file:
    file.write(",".join(light_header) + "\n")

while True:
    light_values = list(read_light_sensors())
    log_data(light_values)
    time.sleep(0.08)
