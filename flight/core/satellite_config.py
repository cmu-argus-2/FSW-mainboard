# Auto-generated from flight.yaml
# Do not edit - changes will be overwritten by the build system.

from micropython import const


class command_config:
    EXIT_STARTUP_TIMEOUT = const(1800)
    DETUMBLING_TIMEOUT_DURATION = const(18000)
    PAYLOAD_TESTING_MODE = False
    BURN_WIRE_TIMEOUT = const(5)


class time_processor_config:
    time_reference = 1735689600


class main_config:
    LOG_LEVEL = "WARNING"


class hal_monitor_config:
    REGULAR_REBOOT = const(86400)


class comms_config:
    HB_PERIOD = const(60)
    AUTH_ENABLED = True
    AUTH_KEY_HEX = "d6172b38acb7d2a28e21662f689d1d15ad78ccc888a9c7a78ef58cb61b0f1e32"
    SC_CALLSIGN = "CT6ARG"
    GS_CALLSIGN = "CS5CEP"


class digipeater_config:
    RX_QUEUE_MAX = const(5)


class hal_config:
    ASIL0_EN = False
