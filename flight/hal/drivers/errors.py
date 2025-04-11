from micropython import const


class Errors:

    # Non-Device Specific Errors
    NO_ERROR = const(0x0)
    DEVICE_NOT_INITIALISED = const(0x1)

    # Error Handling
    INVALID_DEVICE_NAME = const(0x99)  # placeholder value
    DEVICE_DEAD = const(0xFF)  # placeholder value
    REBOOT_DEVICE = const(0xFE)  # placeholder value
    NO_REBOOT = const(0xFD)  # placeholder value


# IMU Errors


# RTC Errors


# GPS Errors


# Radio Errors


# Power Monitor Errors
