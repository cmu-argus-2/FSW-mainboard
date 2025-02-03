import time

import board
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

FUEL_GAUGE_I2C = I2C0
FUEL_GAUGE_I2C_ADDRESS = const(0x36)

fuel_gauge = MAX17205(FUEL_GAUGE_I2C, FUEL_GAUGE_I2C_ADDRESS)

while True:
    print("soc: ", fuel_gauge.read_soc())
    print("capacity: ", fuel_gauge.read_capacity())
    print("current: ", fuel_gauge.read_current())
    print("voltage: ", fuel_gauge.read_voltage())
    print("midvoltage: ", fuel_gauge.read_midvoltage())
    print("cycles: ", fuel_gauge.read_cycles())
    print("tte: ", fuel_gauge.read_tte())
    print("ttf: ", fuel_gauge.read_ttf())
    print("pwrp: ", fuel_gauge.read_time_pwrup())
    time.sleep(1)
