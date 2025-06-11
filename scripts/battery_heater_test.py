import time

import board
import digitalio

enable = digitalio.DigitalInOut(board.HEAT_EN)
enable_heater0 = digitalio.DigitalInOut(board.HEAT0_ON)
enable_heater1 = digitalio.DigitalInOut(board.HEAT1_ON)

enable.direction = digitalio.Direction.OUTPUT
enable_heater0.direction = digitalio.Direction.OUTPUT
enable_heater1.direction = digitalio.Direction.OUTPUT

enable.value = True
enable_heater0.value = True
enable_heater1.value = True

while True:
    print(f"Enable: {enable.value} Heater 0: {enable_heater0.value} Heater 1: {enable_heater1.value}")
    time.sleep(1)
