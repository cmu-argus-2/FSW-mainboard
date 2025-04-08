import time

import board
import digitalio
import supervisor
from busio import I2C
from hal.drivers.max17205 import MAX17205
from micropython import const

I2C0_SDA = board.SDA0  # GPIO0
I2C0_SCL = board.SCL0  # GPIO1

# Line may not be connected, try except sequence
try:
    I2C0 = I2C(I2C0_SCL, I2C0_SDA)
except Exception as e:
    print("Error:", e)
    I2C0 = None

if hasattr(board, "PERIPH_PWR_EN"):
    PERIPH_PWR_EN = digitalio.DigitalInOut(board.PERIPH_PWR_EN)
    PERIPH_PWR_EN.direction = digitalio.Direction.OUTPUT
    PERIPH_PWR_EN.value = True  # Enable peripherals if applicable

FUEL_GAUGE_I2C = I2C0
FUEL_GAUGE_I2C_ADDRESS = const(0x36)

fuel_gauge = MAX17205(FUEL_GAUGE_I2C, FUEL_GAUGE_I2C_ADDRESS)
last_flush_time = time.monotonic()
supervisor.runtime.autoreload = False
fg_data = []
fg_file_path = f"/sd/fg_data_{last_flush_time}.txt"


def flush_to_sd_card():
    global fg_data
    global fg_file_path

    with open(fg_file_path, "a") as fg_file:
        for row in fg_data:
            fg_file.write(",".join(map(str, row)) + "\n")

    fg_data.clear()
    print("Data flushed to SD card")


def log_data(fg_info):
    global last_flush_time
    global fg_data
    current_time = time.monotonic()
    fg_data.append([current_time] + fg_info)

    if time.monotonic() - last_flush_time >= 5000:
        flush_to_sd_card()
        last_flush_time = time.monotonic()


header = ["timestamp_s", "soc", "capacity", "voltage", "vcell", "ocv"]

with open(fg_file_path, "a") as fg_file:
    fg_file.write(",".join(header) + "\n")

while True:
    soc = fuel_gauge.read_soc()
    capacity = fuel_gauge.read_capacity()
    voltage = fuel_gauge.read_voltage()
    vcell = fuel_gauge.read_midvoltage()
    ocv = fuel_gauge.read_ocv()
    print("soc: ", soc)
    print("capacity: ", capacity)
    print("current: ", fuel_gauge.read_current())
    print("voltage: ", voltage)
    print("midvoltage: ", vcell)
    print("vfocv: ", ocv)
    log_data([soc, capacity, voltage, vcell, ocv])
    time.sleep(15)
