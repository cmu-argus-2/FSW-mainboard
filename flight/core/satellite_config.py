# Auto-generated from ground.yaml
# Do not edit - changes will be overwritten by the build system.

from micropython import const


class command_config:
    EXIT_STARTUP_TIMEOUT = const(5)
    DETUMBLING_TIMEOUT_DURATION = const(30)
    BURN_WIRE_TIMEOUT = const(2)
    PAYLOAD_TESTING_MODE = False
    SKIP_DEPLOYMENT = True


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
    AUTH_KEY_HEX = "d6172b38acb7d2a28e21662f689d1d15ad78ccc888a9c7a78ef58cb61b0f1e32"
