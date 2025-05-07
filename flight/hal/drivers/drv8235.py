# The MIT License (MIT)

# Copyright (c) 2022 JG for Cedar Grove Maker Studios

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
`cedargrove_drv8235`
================================================================================

A CircuitPython driver class for the DRV8235 motor controller.


* Author(s): JG, Sebastian Perez, Alena Lu, Perrin Tong

Implementation Notes
--------------------

**Hardware:**

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

"""

from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_register.i2c_bit import ROBit, RWBit
from adafruit_register.i2c_bits import ROBits, RWBits
from hal.drivers.errors import Errors
from micropython import const

# DEVICE REGISTER MAP
_FAULT_STATUS = const(0x00)  # Fault Status Register R-
_RC_STATUS1 = const(0x01)  # Motor Speed status R-
_REG_STATUS1 = const(0x04)  # Output voltage across motor R-
_REG_STATUS2 = const(0x05)  # Current flowing through motor R-
_REG_STATUS3 = const(0x06)  # PWM Duty Cycle R-
_CONFIG0 = const(0x09)  # RW
_CONFIG1 = const(0x0A)  # RW
_CONFIG2 = const(0x0B)  # RW
_CONFIG3 = const(0x0C)  # RW
_CONFIG4 = const(0x0D)  # RW
_REG_CTRL0 = const(0x0E)  # RW
_REG_CTRL1 = const(0x0F)  # RW
_REG_CTRL2 = const(0x10)  # RW
_RC_CTRL2 = const(0x13)  # RW
_RC_CTRL3 = const(0x14)  # RW
_RC_CTRL4 = const(0x15)  # RW
_RC_CTRL7 = const(0x18)  # RW
_RC_CTRL8 = const(0x19)  # RW


"""Fault Register Flag Descriptors
    FAULT  Any fault condition
    STALL  Stall event;
        device disabled, clear fault to reactivate
    OCP    Overcurrent event;
        device disabled, clear fault to reactivate
    OVP    Overvoltage event
    TSD    Overtemperature condition;
        device disabled, resumes with lower temperature
    NPOR   Undervoltage lockout; device disabled,
        resumes with voltage restoration
    """


class BridgeControl:
    """H-bridge PWM control states and descriptors. Bit order: IN2 IN1"""

    COAST = 0b00  # Standby/Coast function (Hi-Z)
    REVERSE = 0b01  # Reverse function
    FORWARD = 0b10  # Forward function
    BRAKE = 0b11  # Brake function

    DESCRIPTOR = ["COAST", "REVERSE", "FORWARD", "BRAKE"]


class DRV8235:
    # class DRV8235(Driver):
    """DC motor driver with I2C interface.

    :param i2c_bus: The microcontroller I2C interface bus pins.
    :param address: The I2C address of the DRV8235 motor controller."""
    # DEFINE I2C DEVICE BITS AND REGISTERS
    _clear = RWBit(_CONFIG0, 1, 1, False)  # Clears fault status flag bits
    _i2c_bc = RWBit(_CONFIG4, 2, 1, False)  # Sets Bridge Control to I2C
    _pmode = RWBit(_CONFIG4, 3, 1, False)  # Sets programming mode to PWM
    _en_out = RWBit(_CONFIG0, 7, 1, False)  # Enables output
    _dir = RWBits(2, _CONFIG4, 0, 1, False)  # Sets direction of h-bridge IN1, IN2
    _reg_ctrl = RWBits(2, _REG_CTRL0, 3, 1, False)  # Sets current/voltage regulation scheme
    _fault = ROBit(_FAULT_STATUS, 7, 1, False)  # Any fault condition
    _stall = ROBit(_FAULT_STATUS, 5, 1, False)  # Stall event
    _ocp = ROBit(_FAULT_STATUS, 4, 1, False)  # Overcurrent event
    _ovp = ROBit(_FAULT_STATUS, 3, 1, False)  # Overvoltage event
    _tsd = ROBit(_FAULT_STATUS, 2, 1, False)  # Overtemperature event
    _npor = ROBit(_FAULT_STATUS, 1, 1, False)  # Undervoltage event
    _wset_vset = RWBits(8, _REG_CTRL1, 0, 1, False)  # Sets target motor voltage
    _vmtr = ROBits(8, _REG_STATUS1, 0, 1, False)
    _imtr = ROBits(8, _REG_STATUS2, 0, 1, False)
    _duty_read = ROBits(6, _REG_STATUS3, 0, 1, False)
    _int_vref = RWBit(_CONFIG3, 4, 1, False)
    _inv_r = RWBits(8, _RC_CTRL3, 0, 1, False)
    _inv_r_scale = RWBits(2, _RC_CTRL2, 6, 1, False)

    # Define Motor Voltage Scaling
    _DRV_MAX_VOLT = 38.00  # Volts
    _COIL_MAX_VOLT = 6.0  # Volts
    _THROTTLE_MAX = _COIL_MAX_VOLT / _DRV_MAX_VOLT

    def __init__(self, i2c_bus, address):
        """Instantiate DRV8235. Set output voltage to 0.0, place into STANDBY
        mode, and reset all fault status flags."""
        self.i2c_device = I2CDevice(i2c_bus, address)
        self._i2c_bc = True
        self._pmode = True
        self._dir = BridgeControl.COAST
        self._reg_ctrl = 0x3  # Sets to voltage regulation
        self._wset_vset = 0  # Sets initial voltage to 0
        self._int_vref = True
        # TODO: check inv_r_scale and inv_r values
        self._inv_r_scale = 0x3
        self._inv_r = 82
        self._en_out = True
        # Clear all fault status flags
        self.clear_faults()

    def index_to_voltage(self, index):
        """Convert an index value to nearest voltage value.
        Scale by 42.67 / 255 = 0.16733 (max output voltage range) precomputed"""
        return index * (0.16733)

    def voltage_to_index(self, volts):
        """Convert a voltage to nearest index value.
        Scale by 255 / 42.67 = 5.9761 precomputed"""
        return round(volts * 5.9761)

    def index_to_current(self, index):
        """Convert an index value to current value.
        Scale by 3.7 / 255 = 0.01451 (max output current range) precomputed"""
        return index * (0.01451)

    def throttle(self):
        """Current motor voltage, ranging from -1.0 (full speed reverse) to
        +1.0 (full speed forward), or ``None`` (controller off). If ``None``,
        the H-bridge is set to high-impedance (coasting). If ``0.0``, the
        H-bridge is set to cause braking."""
        if self.bridge_control[0] == BridgeControl.COAST:
            return None
        if self.bridge_control[0] == BridgeControl.BRAKE:
            return 0.0
        if self.bridge_control[0] == BridgeControl.REVERSE:
            return -1 * round(self._wset_vset / 0xFF, 3) / self._THROTTLE_MAX
        if self.bridge_control[0] == BridgeControl.FORWARD:
            return round(self._wset_vset / 0xFF, 3) / self._THROTTLE_MAX

    def set_throttle(self, new_throttle):
        if new_throttle is None:
            self._wset_vset = 0
            self._dir = BridgeControl.COAST
            return
        # Constrain throttle value
        self._throttle_normalized = min(max(new_throttle * self._THROTTLE_MAX, -self._THROTTLE_MAX), self._THROTTLE_MAX)
        if new_throttle < 0:
            self._wset_vset = int(abs(self._throttle_normalized * 0xFF))
            self._dir = BridgeControl.REVERSE
        elif new_throttle > 0:
            self._wset_vset = int(self._throttle_normalized * 0xFF)
            self._dir = BridgeControl.FORWARD
        else:
            self._wset_vset = 0
            self._dir = BridgeControl.BRAKE
        return

    def throttle_volts(self):
        """Current motor voltage, ranging from -42.7 volts (full speed reverse) to
        +42.7 volts (full speed forward), or ``None`` (controller off). If ``None``,
        the H-bridge is set to high-impedance (coasting). If ``0.0``, the
        H-bridge is set to cause braking."""
        if self.bridge_control[0] == BridgeControl.COAST:
            return None
        if self.bridge_control[0] == BridgeControl.BRAKE:
            return 0.0
        if self.bridge_control[0] == BridgeControl.REVERSE:
            return -1 * self.index_to_voltage(self._wset_vset)
        if self.bridge_control[0] == BridgeControl.FORWARD:
            return self.index_to_voltage(self._wset_vset)

    def set_throttle_volts(self, new_throttle_volts):
        if new_throttle_volts is None:
            self._wset_vset = 0
            self._dir = BridgeControl.COAST
            return
        # Constrain throttle voltage value
        new_throttle_volts = min(max(new_throttle_volts, -42.7), +42.7)
        if new_throttle_volts < 0:
            self._wset_vset = self.voltage_to_index(abs(new_throttle_volts))
            self._dir = BridgeControl.REVERSE
        elif new_throttle_volts > 0:
            self._wset_vset = self.voltage_to_index(new_throttle_volts)
            self._dir = BridgeControl.FORWARD
        else:
            self._wset_vset = 0
            self._dir = BridgeControl.BRAKE
        return

    def throttle_raw(self):
        """Current motor voltage, 8-bit WSET_VSET byte value, ranging from -255 (full speed reverse) to
        255 (full speed forward), or ``None`` (controller off). If ``None``,
        the H-bridge is set to high-impedance (coasting). If ``0``, the
        H-bridge is set to cause braking."""
        if self.bridge_control[0] == BridgeControl.COAST:
            return None
        if self.bridge_control[0] == BridgeControl.BRAKE:
            return 0
        if self.bridge_control[0] == BridgeControl.REVERSE:
            return -1 * self._wset_vset
        if self.bridge_control[0] == BridgeControl.FORWARD:
            return self._wset_vset

    def set_throttle_raw(self, new_throttle_raw):
        if new_throttle_raw is None:
            self._wset_vset = 0
            self._dir = BridgeControl.COAST
            return
        # Constrain raw throttle value
        new_throttle_raw = min(max(new_throttle_raw, -255), 255)
        if new_throttle_raw < 0:
            self._wset_vset = new_throttle_raw
            self._dir = BridgeControl.REVERSE
        elif new_throttle_raw > 0:
            self._wset_vset = new_throttle_raw
            self._dir = BridgeControl.FORWARD
        else:
            self._wset_vset = 0
            self._dir = BridgeControl.BRAKE
        return

    def read_voltage_current(self) -> tuple[float, float]:
        _voltage = self.__read_voltage()
        _current = self.__read_current()
        return (_voltage, _current)

    def __read_voltage(self):
        voltage_index = self._vmtr
        voltage = self.index_to_voltage(voltage_index)
        return voltage

    def __read_current(self):
        current_index = self._imtr
        current = self.index_to_current(current_index)
        return current

    @property
    def bridge_control(self):
        """Motor driver bridge status. Returns the 2-bit bridge control integer
        value and corresponding description string."""
        return self._dir, BridgeControl.DESCRIPTOR[self._dir]

    def clear_faults(self):
        """Clears all fault conditions."""
        self._clear = True  # Clear all fault status flags

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._wset_vset = 0
        self._dir = BridgeControl.COAST

    ######################## ERROR HANDLING ########################

    @property
    def device_errors(self):
        results = []
        if self._fault:
            if self._stall:
                results.append(Errors.TORQUE_COIL_STALL_EVENT)
            if self._ocp:
                results.append(Errors.TORQUE_COIL_OVERCURRENT_EVENT)
            if self._ovp:
                results.append(Errors.TORQUE_COIL_OVERVOLTAGE_EVENT)
            if self._tsd:
                results.append(Errors.TORQUE_COIL_THERMAL_SHUTDOWN)
            if self._npor:
                results.append(Errors.TORQUE_COIL_UNDERVOLTAGE_LOCKOUT)
            self.clear_faults()
        return results

    def deinit(self):
        return
