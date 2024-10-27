"""
torque_coil.py - TorqueCoil Management Class

This class manages the torque for dual or single DRV8830 motor controllers. It provides a simple
interface to set the torque level on the motor(s) and enable or disable the torque coil.

Authors: Gordonson Yan, Harry Rosmann
"""


# TorqueCoil Management Class
class TorqueInterface:
    """Manage torque for dual or single DRV8830 motor controllers."""

    def __init__(self, drv_p, drv_n):
        """
        Initialize the TorqueInterface with one or two DRV8830 instances.

        :param drv1: The first DRV8830 instance in positive direction (required).
        :param drv2: The second DRV8830 instance in negative direction (optional).
        """
        if drv_p is None and drv_n is None:
            raise ValueError("drv1 must not be None")

        self.drv_p = drv_p
        self.drv_n = drv_n

    @property
    def drv_p(self):
        """Get the positive direction DRV8830 instance."""
        return self.drv_p

    @property
    def drv_n(self):
        """Get the negative direction DRV8830 instance."""
        return self.drv_n

    def enable_throttle(self, throttle: float) -> None:
        """
        Enable or disable the torque coil. This effectively enables or disables the motor output.

        :param throttle: Throttle value from -1.0 (full reverse) to +1.0 (full forward).
        """
        if throttle > 1.0 or throttle < -1.0:
            raise ValueError("Throttle must be between -1.0 and 1.0")

        # Set to full speed forward for demonstration
        self.drv_p.set_throttle(throttle)
        if self.drv_n is not None:
            self.drv_n.set_throttle(throttle)

    def enable_volts(self, volts: float) -> None:
        """
        Enable or disable the torque coil. This effectively enables or disables the motor output.

        :param volts: Voltage value from -5.1 (full reverse) to +5.1 (full forward).
        """
        if volts > 5.1 or volts < -5.1:
            raise ValueError("Volts must be between -5.1 and 5.1")

        self.drv_p.set_throttle_volts(volts)
        if self.drv_n is not None:
            self.drv_n.set_throttle_volts(volts)

    def disable(self) -> None:
        """
        Disable the torque coil. This effectively disables the motor output.
        """
        self.drv_p.set_throttle(None)  # Set to None for high-impedance (coast)
        if self.drv_n is not None:
            self.drv_n.set_throttle(None)
