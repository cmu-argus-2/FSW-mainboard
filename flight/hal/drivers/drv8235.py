import sys

import busio

# sys.path.append("/home/sebastian/FSW-mainboard/flight")
from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_register.i2c_bit import ROBit, RWBit
from adafruit_register.i2c_bits import ROBits, RWBits

# from hal.drivers.middleware.errors import Errors
# from hal.drivers.middleware.generic_driver import Driver
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


class VoltageAdapter:
    """Output voltage calculator."""

    def index_to_voltage(self, index):
        """Convert an index value to nearest voltage value."""
        return index * (42.67 / 255)

    def voltage_to_index(self, volts):
        """Convert a voltage to nearest index value."""
        return round(volts * (255 / 42.67))


class BridgeControl:
    """H-bridge PWM control states and descriptors. Bit order: IN2 IN1"""

    COAST = 0b00  # Standby/Coast function (Hi-Z)
    REVERSE = 0b01  # Reverse function
    FORWARD = 0b10  # Forward function
    BRAKE = 0b11  # Brake function

    DESCRIPTOR = ["COAST", "REVERSE", "FORWARD", "BRAKE"]


class Faults:
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

    DESCRIPTOR = ["FAULT", "OCP", "OVP", "UVLO", "TSD"]


class DRV8235:
    # class DRV8235(Driver):
    """DC motor driver with I2C interface.

    :param i2c_bus: The microcontroller I2C interface bus pins.
    :param address: The I2C address of the DRV8235 motor controller."""

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
        self._inv_r_scale = 0x3
        self._inv_r = 82
        self._en_out = True
        # Clear all fault status flags
        self.clear_faults()

        super().__init__()

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
            return -1 * round(self._wset_vset / 0xFF, 3)
        return round(self._wset_vset / 0xFF, 3)

    def set_throttle(self, new_throttle):
        if new_throttle is None:
            self._wset_vset = 0
            self._dir = BridgeControl.COAST
            return
        # Constrain throttle value
        self._throttle_normalized = min(max(new_throttle, -1.0), +1.0)
        if new_throttle < 0:
            self._wset_vset = int(abs(new_throttle * 0xFF))
            self._dir = BridgeControl.REVERSE
        elif new_throttle > 0:
            self._wset_vset = int(new_throttle * 0xFF)
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
            return -1 * VoltageAdapter.index_to_voltage(self, self._wset_vset)
        return VoltageAdapter.index_to_voltage(self, self._wset_vset)

    def set_throttle_volts(self, new_throttle_volts):
        if new_throttle_volts is None:
            self._wset_vset = 0
            self._dir = BridgeControl.COAST
            return
        # Constrain throttle voltage value
        new_throttle_volts = min(max(new_throttle_volts, -42.7), +42.7)
        if new_throttle_volts < 0:
            self._wset_vset = VoltageAdapter.voltage_to_index(self, abs(new_throttle_volts))
            self._dir = BridgeControl.REVERSE
        elif new_throttle_volts > 0:
            self._wset_vset = VoltageAdapter.voltage_to_index(self, new_throttle_volts)
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

    @property
    def bridge_control(self):
        """Motor driver bridge status. Returns the 2-bit bridge control integer
        value and corresponding description string."""
        return self._dir, BridgeControl.DESCRIPTOR[self._dir]

    @property
    def fault(self):
        """Motor driver fault register status. Returns state of FAULT flag and
        a list of activated fault flag descriptors. FAULT flag is ``True`` if
        one or more fault register flags are ``True``."""
        faults = []
        if self._fault:
            faults.append(Faults.DESCRIPTOR[0])
            if self._ocp:
                faults.append(Faults.DESCRIPTOR[1])
            if self._uvlo:
                faults.append(Faults.DESCRIPTOR[2])
            if self._ots:
                faults.append(Faults.DESCRIPTOR[3])
            if self._ilimit:
                faults.append(Faults.DESCRIPTOR[4])
        return self._fault, faults

    def clear_faults(self):
        """Clears all fault conditions."""
        self._clear = True  # Clear all fault status flags

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._wset_vset = 0
        self._dir = BridgeControl.STANDBY

    """
    ----------------------- HANDLER METHODS -----------------------
    """


#     @property
#     def get_flags(self):
#         flags = {}
#         if self._fault:
#             if self._stall:
#                 flags["stall"] = None
#             if self._ocp:
#                 flags["ocp"] = None
#             if self._ovp:
#                 flags["ovp"] = None
#             if self._tsd:
#                 flags["tsd"] = None
#             if self._npor:
#                 flags["npor"] = None
#         return flags

######################### DIAGNOSTICS #########################

#     def __check_for_faults(self) -> list[int]:
#         """_check_for_faults: Checks for any device faluts returned by fault function in DRV8235

#         :return: List of errors that exist in the fault register
#         """
#         faults_flag, faults = self.fault

#         if not faults_flag:
#             return [Errors.NOERROR]

#         errors: list[int] = []

#         if "STALL" in faults:
#             errors.append(Errors.DRV8235_STALL_EVENT)
#         if "OCP" in faults:
#             errors.append(Errors.DRV8235_OVERCURRENT_LOCKOUT)
#         if "OVP" in faults:
#             errors.append(Errors.DRV8235_OVERVOLTAGE_CONDITION)
#         if "TSD" in faults:
#             errors.append(Errors.DRV8235_OVERTEMPERATURE_EVENT)
#         if "NPOR" in faults:
#             errors.append(Errors.DRV8235_UNDERVOLTAGE_EVENT)

#         self.clear_faults()

#         return errors

#     def __throttle_tests(self) -> int:
#         """_throttle_tests: Checks for any throttle errors in DRV8235, whether the returned reading is
#         outside of the set range indicated in the driver file

#         :return: true if test passes, false if fails
#         """
#         throttle_volts_val = self.throttle_volts()
#         if throttle_volts_val is not None:
#             if (throttle_volts_val < -42.67) or (throttle_volts_val > 42.67):
#                 return Errors.DRV8235_THROTTLE_OUTSIDE_RANGE

#         throttle_raw_val = self.throttle_raw()
#         if throttle_raw_val is not None:
#             if (throttle_raw_val < -255) or (throttle_raw_val > 255):
#                 return Errors.DRV8235_THROTTLE_OUTSIDE_RANGE

#         return Errors.NOERROR

#     def run_diagnostics(self) -> list[int] | None:
#         """run_diagnostic_test: Run all tests for the component"""
#         error_list: list[int] = []

#         error_list = self.__check_for_faults()
#         error_list.append(self.__throttle_tests())

#         error_list = list(set(error_list))

#         if Errors.NOERROR not in error_list:
#             self.errors_present = True

#         return error_list
