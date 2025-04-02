import time

import board
import digitalio
from busio import I2C
from hal.drivers.opt4003 import OPT4003

PERIPH_PWR_EN = digitalio.DigitalInOut(board.PERIPH_PWR_EN)
PERIPH_PWR_EN.direction = digitalio.Direction.OUTPUT
PERIPH_PWR_EN.value = True

PERIPH_PWR_OVC = digitalio.DigitalInOut(board.PERIPH_PWR_FLT)
PERIPH_PWR_OVC.direction = digitalio.Direction.INPUT

# DO NOT MOVE
time.sleep(2)  # Wait for peripherals to power up

I2C0_SDA = board.SDA0
I2C0_SCL = board.SCL0

# Line may not be connected, try except sequence
try:
    I2C0 = I2C(I2C0_SCL, I2C0_SDA, frequency=400000)
except Exception:
    print("I2C0 not found")
    I2C0 = None
try:
    address = 0x44
    bus = I2C0
    light_sensor = OPT4003(
        bus,
        address,
    )

except Exception as e:
    print(e)
