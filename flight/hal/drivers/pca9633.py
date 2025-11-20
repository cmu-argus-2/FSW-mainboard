"""
`pca9633`
====================================================

CircuitPython driver for the pca9633

* Author(s): Varun Rajesh, Perrin Tong

Implementation Notes
--------------------

"""

from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_register.i2c_bits import RWBits
from micropython import const

_NEGATED = True  # Values seems negated
_PWM_MIN = const(0)
_PWM_MAX = const(255)


class PCA9633:
    # MODE1 bits
    _sleep = RWBits(1, 0x00, 4)  # SLEEP bit in MODE1 (0 = on, 1 = sleep)
    # MODE2 bits
    _outdrv = RWBits(1, 0x01, 2)  # OUTDRV bit in MODE2 (0 = open-drain, 1 = totem-pole)

    # LEDOUT and PWM
    _channel_enable = RWBits(8, 0x08, 0)  # LEDOUT
    _pwm_channel_0 = RWBits(8, 0x02, 0)
    _pwm_channel_1 = RWBits(8, 0x03, 0)
    _pwm_channel_2 = RWBits(8, 0x04, 0)
    _pwm_channel_3 = RWBits(8, 0x05, 0)

    _MODE_SELECTION = 0b10101010

    def __init__(self, i2c, address=0x60):
        self.i2c_device = I2CDevice(i2c, address)
        self.i2c = i2c

        self._sleep = 0
        self._outdrv = 1

        self.turn_off_pwm(3)
        self.turn_off_pwm(0)
        self.turn_off_pwm(1)
        self.turn_off_pwm(2)

    def set_pwm(self, channel, value):
        value = (_PWM_MAX - value) if _NEGATED else value
        if channel == 0:
            self._channel_enable = self._channel_enable & 0b11111100 | 0b00000010
            self._pwm_channel_0 = value
        elif channel == 1:
            self._channel_enable = self._channel_enable & 0b11110011 | 0b00001000
            self._pwm_channel_1 = value
        elif channel == 2:
            self._channel_enable = self._channel_enable & 0b11001111 | 0b00100000
            self._pwm_channel_2 = value
        elif channel == 3:
            self._channel_enable = self._channel_enable & 0b00111111 | 0b10000000
            self._pwm_channel_3 = value
        else:
            raise ValueError("Channel must be between 0 and 3.")

    def turn_off_pwm(self, channel):
        self.set_pwm(channel, _PWM_MIN)
        if channel == 0:
            self._channel_enable = self._channel_enable & 0b11111100 | 0b00000001
        elif channel == 1:
            self._channel_enable = self._channel_enable & 0b11110011 | 0b00000100
        elif channel == 2:
            self._channel_enable = self._channel_enable & 0b11001111 | 0b00010000
        elif channel == 3:
            self._channel_enable = self._channel_enable & 0b00111111 | 0b01000000
        else:
            raise ValueError("Channel must be between 0 and 3.")

    def enable_driver(self):
        self.set_pwm(3, _PWM_MAX)
        self._sleep = 0

    def disable_driver(self):
        self.set_pwm(3, _PWM_MIN)
        self.set_pwm(0, _PWM_MIN)
        self.set_pwm(1, _PWM_MIN)
        self.set_pwm(2, _PWM_MIN)
        self._sleep = 1

    ######################## ERROR HANDLING ########################

    @property
    def device_errors(self):
        return []

    def deinit(self):
        return
