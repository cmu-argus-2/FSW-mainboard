import time
import digitalio
import board

led = digitalio.DigitalInOut(board.JETSON_EN)
led.direction = digitalio.Direction.OUTPUT

led.value = True

while True:
    time.sleep(0.1)