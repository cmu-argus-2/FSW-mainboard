"""
StateFlags: Class for managing flags and counters in the NVM.

This class is used to manage the state flags and counters in the NVM. It is also
used to keep track of the state of the system and to store the number of times
a particular event has occurred.

Author: Harry Rosmann

"""

from hal.drivers.bitflags import bitFlag, multiBitFlag
from micropython import const


class StateFlags:
    """StateFlags: Class for managing flags and counters in the NVM."""

    def __init__(self):
        pass

    # TODO: Update to reflect desired design

    # NVM register numbers
    BOOTCNT = const(0)
    VBUSRST = const(6)
    STATECNT = const(7)
    TOUTS = const(9)
    GSRSP = const(10)
    ICHRG = const(11)
    FLAG = const(16)

    # General NVM counters
    c_boot = multiBitFlag(register=BOOTCNT, lowest_bit=0, num_bits=8)
    c_vbusrst = multiBitFlag(register=VBUSRST, lowest_bit=0, num_bits=8)
    c_state_err = multiBitFlag(register=STATECNT, lowest_bit=0, num_bits=8)
    c_gs_resp = multiBitFlag(register=GSRSP, lowest_bit=0, num_bits=8)
    c_ichrg = multiBitFlag(register=ICHRG, lowest_bit=0, num_bits=8)

    # Define NVM flags
    f_lowbatt = bitFlag(register=FLAG, bit=0)
    f_solar = bitFlag(register=FLAG, bit=1)
    f_gpson = bitFlag(register=FLAG, bit=2)
    f_lowbtout = bitFlag(register=FLAG, bit=3)
    f_gpsfix = bitFlag(register=FLAG, bit=4)
    f_shtdwn = bitFlag(register=FLAG, bit=5)
