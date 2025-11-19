from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_register.i2c_bits import RWBits
from micropython import const

_ENABLE = const(0b00000001)
_DISABLE = const(0b00000000)


class PCA9633:
    # MODE1 bits
    _mode1 = RWBits(1, 0x00, 0)  # MODE1 register
    _sleep = RWBits(1, 0x00, 4)  # SLEEP bit in MODE1 (0 = on, 1 = sleep)
    # MODE2 bits
    _outdrv = RWBits(1, 0x01, 2)  # OUTDRV bit in MODE2 (0 = open-drain, 1 = totem-pole)

    # LEDOUT and PWM
    _channel_enable = RWBits(8, 0x08, 0)  # LEDOUT
    _pwm_channel_0 = RWBits(8, 0x02, 0)
    _pwm_channel_1 = RWBits(8, 0x03, 0)
    _pwm_channel_2 = RWBits(8, 0x04, 0)
    _pwm_channel_3 = RWBits(8, 0x05, 0)

    _MODE_SELECTION = 0b10101010  # LED3 on, 0-2 PWM

    def __init__(self, i2c, address=0x60):
        self.i2c_device = I2CDevice(i2c, address)
        self.i2c = i2c

        # Wake up oscillator
        self._sleep = 0

        self._mode1 = 1

        # Ensure totem-pole outputs if that’s what your hardware wants
        self._outdrv = 1

        # Configure channel modes (LED3 on, 0-2 off)
        # 10: ON
        # 01: possibly pwm
        self.set_pwm(3, 255)  # 0
        self.set_pwm(0, 255)  # 0
        self.set_pwm(1, 255)  # 0
        self.set_pwm(2, 255)
        self._channel_enable = self._MODE_SELECTION

    def set_pwm(self, channel, value):
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
        # Wake and restore LEDOUT config
        self.set_pwm(3, 0)
        self._sleep = 0
        # self._channel_enable = self._MODE_SELECTION

    def disable_driver(self):
        # Optional: real low-power disable
        # self._channel_enable = 0b  # all LEDs off
        self.set_pwm(3, 255)  # 0
        self.set_pwm(0, 255)  # 0
        self.set_pwm(1, 255)  # 0
        self.set_pwm(2, 255)
        self._sleep = 1

    def deinit(self):
        # You might want to call disable_driver() here
        self.disable_driver()
