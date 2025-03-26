import time

import board
import busio

I2C1 = busio.I2C(board.SCL1, board.SDA1)

while True:
    while not I2C1.try_lock():
        pass

    driver_strength = 0
    # Set to Totem Pole Mode
    I2C1.writeto(0x60, bytes([0x01, 0b00000001]))

    # Enable channel 3, Put 0-2 into PWM Mode
    I2C1.writeto(0x60, bytes([0x08, 0b01101010]))

    # Set PWM drive of channels 0-2
    I2C1.writeto(0x60, bytes([0x02, driver_strength]))
    I2C1.writeto(0x60, bytes([0x03, driver_strength]))
    I2C1.writeto(0x60, bytes([0x04, driver_strength]))

    # Enable driver
    I2C1.writeto(0x60, bytes([0x00, 0b00000001]))

    I2C1.unlock()

    time.sleep(1)
