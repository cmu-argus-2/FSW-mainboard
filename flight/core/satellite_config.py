# Auto-generated from ground.yaml
# Do not edit - changes will be overwritten by the build system.

from micropython import const


class adcs_config:
    CONTROLLER_MODE = 0


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


# TODO: Change the auth key before flight


class comms_config:
    ARGUS_ID = const(0)
    HB_PERIOD = const(60)
    AUTH_ENABLED = True
    AUTH_KEY_HEX = "d6172b38acb7d2a28e21662f689d1d15ad78ccc888a9c7a78ef58cb61b0f1e32"
    SC_CALLSIGN = "CT6ARG"
    GS_CALLSIGN = "CS5CEP"
