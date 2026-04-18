"""
Script to turn the jetson on or off.
"""
import digitalio
import board
from busio import I2C

JETSON_ENABLE = digitalio.DigitalInOut(board.JETSON_EN)
JETSON_ENABLE.direction = digitalio.Direction.OUTPUT

print("Jetson Enable Pin:", JETSON_ENABLE.value)

JETSON_ENABLE.value = True
    
print("Jetson Enable Pin:", JETSON_ENABLE.value)

# Wait for the jetson to boot up
import time
time.sleep(60)

# wait for user to ask to turn off the jetson
input("Press Enter to turn off the jetson...")
JETSON_ENABLE.value = False
print("Jetson Enable Pin:", JETSON_ENABLE.value)
