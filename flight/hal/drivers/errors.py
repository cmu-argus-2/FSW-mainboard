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
    RTC_LOST_POWER = const(0x10)
    RTC_BATTERY_LOW = const(0x11)

    # GPS Errors
    GPS_UPDATE_CHECK_FAILED = const(0x20)

    # Radio Errors

    # Power Monitor Errors
    PWR_MON_COULD_NOT_TURN_ON = const(0xA0)
    PWR_MON_VOLTAGE_OUT_OF_RANGE = const(0xA1)
    PWR_MON_ADC_OC_OVERCURRENT_MAX = const(0xA2)
    PWR_MON_ADC_ALERT_OVERCURRENT_MAX = const(0xA3)
    PWR_MON_NOT_CONNECTED_TO_POWER = const(0xA4)

    # TORQUE COIL ERRORS
    TORQUE_COIL_OVERCURRENT_EVENT = const(0xB0)
    TORQUE_COIL_UNDERVOLTAGE_LOCKOUT = const(0xB1)
    TORQUE_COIL_OVERTEMP_EVENT = const(0xB2)
    TORQUE_COIL_EXTENDED_CURRENT_LIMIT_EVENT = const(0xB3)
    TORQUE_COIL_THROTTLE_OUTSIDE_RANGE = const(0xB4)

    # LIGHT SENSOR ERRORS
    LIGHT_SENSOR_ID_CHECK_FAILED = const(0xC0)
    LIGHT_SENSOR_CRC_COUNTER_TEST_FAILED = const(0xC1)
