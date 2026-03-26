"""
COMMS operating mode definitions.
"""

from micropython import const


class COMMS_MODE:
    STANDARD = const(0x01)  # Default behavior
    RF_STOP = const(0x02)  # Hard TX stop latch
    # Backwards-compatible alias for existing code paths.
    NORMAL = STANDARD

    ALL = (STANDARD, RF_STOP)


COMMS_MODE_STR = {
    COMMS_MODE.STANDARD: "STANDARD",
    COMMS_MODE.RF_STOP: "RF_STOP",
}
