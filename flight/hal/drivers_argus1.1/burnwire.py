"""
This module contains the BurnWires class which provides functionality for controlling burn wires.

Author: Harry Rosmann
Date: March 28, 2024
"""

from time import sleep

from digitalio import DigitalInOut, DriveMode
from hal.drivers.middleware.generic_driver import Driver
from micropython import const
from pwmio import PWMOut


class BurnWires(Driver):
    """
    The BurnWires class provides functionality for controlling burn wires.

    Attributes:
        INITIAL_FREQUENCY_HZ (int): The initial frequency in Hz for the PWM signal.
        INITIAL_DUTY_PCT (int): The initial duty cycle percentage for the PWM signal.
        INITIAL_DURATION_S (int): The initial duration in seconds for burning.

        DUTY_CYCLE_OFF (int): The duty cycle value to turn off the burn wire.

    Methods:
        __init__(self, enable_pin, burn_xp, burn_xm, burn_yp, burn_ym): Initializes the BurnWires object.
        enable(self): Enables the burn wires through the relay.
        disable(self): Disables the burn wires through the relay.
        burn_xp(self): Burns the positive X-axis wire.
        burn_xm(self): Burns the negative X-axis wire.
        burn_yp(self): Burns the positive Y-axis wire.
        burn_ym(self): Burns the negative Y-axis wire.
    """

    # Initial values for the attributes
    INITIAL_FREQUENCY_HZ = const(1000)
    INITIAL_DUTY_PCT = const(50)
    INITIAL_DURATION_S = const(1)

    # Duty cycle value to turn off the burn wire
    DUTY_CYCLE_OFF = const(0)

    def __init__(self, enable_pin, burn_xp, burn_xm, burn_yp, burn_ym):
        """
        Initializes the BurnWires object.

        Args:
            enable_pin: The pin used to enable/disable the burn wires.
            burn_xp: The pin used for burning the positive X-axis wire.
            burn_xm: The pin used for burning the negative X-axis wire.
            burn_yp: The pin used for burning the positive Y-axis wire.
            burn_ym: The pin used for burning the negative Y-axis wire.
        """
        self.__pwm_frequency = self.INITIAL_FREQUENCY_HZ
        self.__duty_cycle = self.INITIAL_DUTY_PCT
        self.__burn_duration = self.INITIAL_DURATION_S

        self.__enable = self.__configure_enable(enable_pin)

        self.__burn_xp = self.__configure_burn_pin(burn_xp)
        self.__burn_xm = self.__configure_burn_pin(burn_xm)
        self.__burn_yp = self.__configure_burn_pin(burn_yp)
        self.__burn_ym = self.__configure_burn_pin(burn_ym)

        super().__init__(self.__enable)

    def frequency_hz(self):
        """
        Get the current frequency in Hz for the PWM signal.
        """
        return self.__pwm_frequency

    def set_frequency_hz(self, frequency_hz):
        """
        Set the frequency in Hz for the PWM signal.

        Args:
            frequency_hz: The frequency in Hz for the PWM signal.
        """
        self.__pwm_frequency = frequency_hz

    def duty_cycle_pct(self):
        """
        Get the current duty cycle percentage for the PWM signal.
        """
        return self.__duty_cycle

    def set_duty_cycle_pct(self, duty_cycle_pct):
        """
        Set the duty cycle percentage for the PWM signal.

        Args:
            duty_cycle_pct: The duty cycle percentage for the PWM signal.
        """
        self.__duty_cycle = duty_cycle_pct

    def duration_s(self):
        """
        Get the current duration in seconds for burning.
        """
        return self.__burn_duration

    def set_duration_s(self, duration_s):
        """
        Set the duration in seconds for burning.

        Args:
            duration_s: The duration in seconds for burning.
        """
        self.__burn_duration = duration_s

    def __turn_off_all_burns(self) -> None:
        """__turn_off_all_burns: turns off all the burn wires"""
        self.__burn_xp.duty_cycle = self.DUTY_CYCLE_OFF
        self.__burn_xm.duty_cycle = self.DUTY_CYCLE_OFF
        self.__burn_yp.duty_cycle = self.DUTY_CYCLE_OFF
        self.__burn_ym.duty_cycle = self.DUTY_CYCLE_OFF

    def reset(self):
        """reset: Turns off an on the relay to turn off an on the burn wires.

        Turns off all burn wire duty cycles to be safe.
        """
        self.disable()
        self.__turn_off_all_burns(self)
        self.enable()

    def enable(self):
        """
        Enables the burn wires through the relay.
        """
        self.__enable.drive_mode = DriveMode.PUSH_PULL
        self.__enable.value = True

    def disable(self):
        """
        Disables the burn wires through the relay.
        """
        self.__enable.value = False
        self.__enable.drive_mode = DriveMode.OPEN_DRAIN

    def __configure_enable(self, enable_pin):
        """
        Configures the enable pin for burn wires.

        Args:
            enable_pin: The pin used to enable/disable the burn wires.

        Returns:
            The configured enable pin.
        """
        enable_pin = DigitalInOut(enable_pin)
        enable_pin.switch_to_output(drive_mode=DriveMode.OPEN_DRAIN)

        return enable_pin

    def __configure_burn_pin(self, burn_pin):
        """
        Configures a burn pin for burning wires.

        Args:
            burn_pin: The pin used for burning a wire.

        Returns:
            The configured burn pin.
        """
        # Set the duty cycle to 0 so it doesn't start burning
        burn_wire = PWMOut(
            burn_pin,
            frequency=self.frequency_hz,
            duty_cycle=self.DUTY_CYCLE_OFF,
        )

        return burn_wire

    def __burn(self, burn_wire):
        """
        Burns a wire using the specified burn pin.

        Args:
            burn_wire: The burn pin used for burning a wire.
        """
        self.duty_cycle_pct = self.duty_cycle_pct
        sleep(self.duration_s)
        self.duty_cycle_pct = self.DUTY_CYCLE_OFF

    def burn_xp(self):
        """
        Burns the positive X-axis wire.
        """
        self.__burn(self.__burn_xp)

    def burn_xm(self):
        """
        Burns the negative X-axis wire.
        """
        self.__burn(self.__burn_xm)

    def burn_yp(self):
        """
        Burns the positive Y-axis wire.
        """
        self.__burn(self.__burn_yp)

    def burn_ym(self):
        """
        Burns the negative Y-axis wire.
        """
        self.__burn(self.__burn_ym)

    """
    ----------------------- HANDLER METHODS -----------------------
    """

    def get_flags(self):
        return {}
