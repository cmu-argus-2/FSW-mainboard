from micropython import const

"""
TODO State descriptions here

"""


class STATES:
    STARTUP = const(0x00)
    NOMINAL = const(0x01)
    DOWNLINK = const(0x02)
    LOW_POWER = const(0x03)
    SAFE = const(0x04)


STR_STATES = ["STARTUP", "NOMINAL", "DOWNLINK", "LOW_POWER", "SAFE"]


# TODO Define all transition functions here
