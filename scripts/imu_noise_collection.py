import time

import circuitpython_csv as csv
import supervisor
from hal.configuration import SATELLITE

print("Booting ARGUS-1...")
boot_errors = SATELLITE.boot_sequence()
print("ARGUS-1 booted.")
print(f"Boot Errors: {boot_errors}")
mag_data = []
gyro_data = []
last_flush_time = time.monotonic()
current_time = time.localtime()
date = SATELLITE.RTC.datetime
formatted_time = f"{date.tm_year}-{date.tm_mon:02d}-{date.tm_mday:02d}_{date.tm_hour:02d}-{date.tm_min:02d}-{date.tm_sec:02d}"
supervisor.runtime.autoreload = False
mag_file_path = f"/sd/magnetometer_data_{formatted_time}.csv"
gyro_file_path = f"/sd/gyroscope_data_{formatted_time}.csv"


def flush_to_sd_card():
    global mag_data
    global gyro_data
    global mag_file_path
    global gyro_file_path

    with open(mag_file_path, "a") as mag_file:
        mag_writer = csv.writer(mag_file)
        mag_writer.writerows(mag_data)

    with open(gyro_file_path, "a") as gyro_file:
        gyro_writer = csv.writer(gyro_file)
        gyro_writer.writerows(gyro_data)

    # Clear the data after flushing
    mag_data.clear()
    gyro_data.clear()
    print("Data flushed to SD card.")


def log_data(mag, gyro):
    global last_flush_time
    global mag_data
    global gyro_data
    current_time_ns = int(time.monotonic() * 1e9)
    mag_data.append([current_time_ns] + mag)
    gyro_data.append([current_time_ns] + gyro)

    if time.monotonic() - last_flush_time >= 30:
        flush_to_sd_card()
        last_flush_time = time.monotonic()


mag_header = ["timestamp_ns", "mag_x", "mag_y", "mag_z"]
gyro_header = ["timestamp_ns", "gyro_x", "gyro_y", "gyro_z"]

with open(mag_file_path, "a") as mag_file:
    mag_writer = csv.writer(mag_file)
    mag_writer.writerow(mag_header)

with open(gyro_file_path, "a") as gyro_file:
    gyro_writer = csv.writer(gyro_file)
    gyro_writer.writerow(gyro_header)

while True:
    mag = list(SATELLITE.IMU.mag())
    gyro = list(SATELLITE.IMU.gyro())
    log_data(mag, gyro)
    time.sleep(0.08)
