# Auto-generated from ground.yaml
# Do not edit - changes will be overwritten by the build system.

from micropython import const


class command_config:
    EXIT_STARTUP_TIMEOUT = const(5)
    DETUMBLING_TIMEOUT_DURATION = const(30)
    BURN_WIRE_TIMEOUT = const(2)


class time_processor_config:
    time_reference = 1735689600


class main_config:
    LOG_LEVEL = "INFO"


class hal_monitor_config:
    REGULAR_REBOOT = const(3600)
