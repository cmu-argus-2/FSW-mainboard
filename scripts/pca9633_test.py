import time

import board
import busio
import digitalio

if hasattr(board, "PERIPH_PWR_EN"):
    PERIPH_PWR_EN = digitalio.DigitalInOut(board.PERIPH_PWR_EN)
    PERIPH_PWR_EN.direction = digitalio.Direction.OUTPUT
    PERIPH_PWR_EN.value = True  # Enable peripherals if applicable

print("Enabled 3.3V peripheral line")

# Wait for a bit to allow PCA9633 to boot
time.sleep(3)

# For mainboard v2s, use I2C1
# For mainboard v3s (default) use I2C0
I2C0_SDA = board.SDA0  # GPIO0
I2C0_SCL = board.SCL0  # GPIO1

# Line may not be connected, try except sequence
try:
    I2C0 = busio.I2C(I2C0_SCL, I2C0_SDA)
except Exception as e:
    print("Error:", e)
    I2C0 = None

while True:
    while not I2C0.try_lock():
        pass

    print("I2C0 unlocked")

    """
    Driver strength is the power level for the burn-wires.
    CAUTION: if the strength is too high the board might brown-out
    """
    driver_strength = 0

    # Set to Totem Pole Mode
    I2C0.writeto(0x60, bytes([0x01, 0b00000001]))

    # Enable channel 3, Put 0-2 into PWM Mode
    I2C0.writeto(0x60, bytes([0x08, 0b01101010]))

    # Set PWM drive of channels 0-2
    I2C0.writeto(0x60, bytes([0x02, driver_strength]))
    I2C0.writeto(0x60, bytes([0x03, driver_strength]))
    I2C0.writeto(0x60, bytes([0x04, driver_strength]))

    print("Burn wires set")

    # Enable driver
    I2C0.writeto(0x60, bytes([0x00, 0b00000001]))

    print("Burn wires enabled")

    I2C0.unlock()

    print("Waiting for 5s")
    time.sleep(5)
