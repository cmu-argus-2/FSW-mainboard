# GS Command Definitions
from micropython import const


class CMD_ID:
    FORCE_REBOOT = const(0x40)
    SWITCH_TO_STATE = const(0x41)
    UPLINK_TIME_REFERENCE = const(0x42)
    UPLINK_ORBIT_REFERENCE = const(0x43)
    TURN_OFF_PAYLOAD = const(0x44)
    SCHEDULE_OD_EXPERIMENT = const(0x45)

    REQUEST_TM_HEARTBEAT = const(0x46)
    REQUEST_TM_HAL = const(0x47)
    REQUEST_TM_STORAGE = const(0x48)
    REQUEST_TM_PAYLOAD = const(0x49)

    REQUEST_FILE_METADATA = const(0x4A)
    REQUEST_FILE_PKT = const(0x4B)
    REQUEST_IMAGE = const(0x4C)

    DOWNLINK_ALL = const(0x4D)
