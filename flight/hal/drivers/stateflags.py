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

    # NVM register numbers
    LOG_LVL = const(0)
    FLAG = const(1)

    # Define NVM flags
    f_log_level = multiBitFlag(register=LOG_LVL, lowest_bit=0, num_bits=8)
    f_rf_stop = bitFlag(register=FLAG, bit=0)
