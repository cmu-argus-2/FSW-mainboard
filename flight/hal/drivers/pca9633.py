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

_CIRCUIT_NEGATED = False
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

        self.set_pwm(3, _PWM_MIN)
        self.set_pwm(0, _PWM_MIN)
        self.set_pwm(1, _PWM_MIN)
        self.set_pwm(2, _PWM_MIN)
        self.nnel_enable = self._MODE_SELECTION

    def set_pwm(self, channel, value):
        value = (_PWM_MAX - value) if _CIRCUIT_NEGATED else value
        if channel == 0:
            self._pwm_channel_0 = value
        elif channel == 1:
            self._pwm_channel_1 = value
        elif channel == 2:
            self._pwm_channel_2 = value
        elif channel == 3:
            self._pwm_channel_3 = value
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
