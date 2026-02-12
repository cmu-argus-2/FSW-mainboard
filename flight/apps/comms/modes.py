"""
COMMS operating mode definitions.

These modes control RF/comms behavior without changing the global
spacecraft mission state machine.
"""

from micropython import const


class COMMS_MODE:
    QUIET = const(0x01)  # No periodic heartbeat TX; commanding still available
    NORMAL = const(0x02)  # Default behavior
    DIGIPEAT = const(0x03)  # Enable digipeater relay behavior
    RF_STOP = const(0x04)  # Hard TX stop latch

    ALL = (QUIET, NORMAL, DIGIPEAT, RF_STOP)


COMMS_MODE_STR = {
    COMMS_MODE.QUIET: "QUIET",
    COMMS_MODE.NORMAL: "NORMAL",
    COMMS_MODE.DIGIPEAT: "DIGIPEAT",
    COMMS_MODE.RF_STOP: "RF_STOP",
}
