# Auto-generated from ground.yaml
# Do not edit - changes will be overwritten by the build system.

from micropython import const


class command_config:
    EXIT_STARTUP_TIMEOUT = const(5)
    DETUMBLING_TIMEOUT_DURATION = const(30)
    BURN_WIRE_TIMEOUT = const(2)
    PAYLOAD_TESTING_MODE = False


class time_processor_config:
    time_reference = 1735689600


class main_config:
    LOG_LEVEL = "INFO"


class hal_monitor_config:
    REGULAR_REBOOT = const(3600)


class comms_config:
    ARGUS_ID = const(0x0)
    HB_PERIOD = const(30)
    AUTH_ENABLED = True
    AUTH_KEY_HEX = "5764d937fc846da8e88c8abb39cbaaaa25b6c22cbbb75b79276341354f1a2e88"
    SC_CALLSIGN = "CT6xxx"
    GS_CALLSIGN = "CSXXXX"
