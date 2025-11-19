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

_ENABLE = const(0b00000001)
_DISABLE = const(0b00000000)


class PCA9633:
    """Driver for the PCA9633 I2C LED driver."""

    # Register definitions
    _totem_pole_mode = RWBits(8, 0x01, 0)  # Totem Pole Mode (bit 0 of register 0x01)
    _channel_enable = RWBits(8, 0x08, 0)  # Channel enable/mode (register 0x08)
    _pwm_channel_0 = RWBits(8, 0x02, 0)  # PWM value for channel 0 (register 0x02)
    _pwm_channel_1 = RWBits(8, 0x03, 0)  # PWM value for channel 1 (register 0x03)
    _pwm_channel_2 = RWBits(8, 0x04, 0)  # PWM value for channel 2 (register 0x04)
    _pwm_channel_3 = RWBits(8, 0x05, 0)  # PWM value for channel 3 (register 0x05)
    _driver_enable = RWBits(8, 0x00, 0)  # Driver enable (bit 0 of register 0x00)

    _MODE_SELECTION = 0b01101010

    def __init__(self, i2c, address=0x60):
        """
        Initialize the PCA9633 driver.

        :param i2c: The I2C bus object.
        :param address: The I2C address of the PCA9633 (default: 0x60).
        """
        self.i2c_device = I2CDevice(i2c, address)
        self.i2c = i2c
        self._totem_pole_mode = _ENABLE
        self._channel_enable = self._MODE_SELECTION

    def set_pwm(self, channel, value):
        """
        Set the PWM drive strength for a specific channel.

        :param channel: The channel number (0-3).
        :param value: The PWM value (0-255).
        """
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
        """Enable the PCA9633 driver."""
        self._driver_enable = _ENABLE

    def disable_driver(self):
        """Disable the PCA9633 driver."""
        self._driver_enable = _DISABLE
        self._channel_enable = _DISABLE

    ######################## ERROR HANDLING ########################

    @property
    def device_errors(self):
        return []

    def deinit(self):
        """Deinitialize the PCA9633 driver."""
        return
