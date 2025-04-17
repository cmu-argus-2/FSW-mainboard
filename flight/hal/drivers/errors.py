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
    IMU_ERROR_CODE = const(0x2)  # placeholder value
    IMU_DROP_COMMAND_ERROR = const(0x3)  # placeholder value
    IMU_FATAL_ERROR = const(0x4)  # placeholder value

    # RTC Errors
    RTC_LOST_POWER = const(0x10)  # placeholder value
    RTC_BATTERY_LOW = const(0x11)  # placeholder value

    # GPS Errors
    GPS_UPDATE_CHECK_FAILED = const(0x20)  # placeholder value

    # Radio Errors

    # Power Monitor Errors
    PWR_MON_ADC_ALERT_OVERCURRENT = const(0xA5)  # placeholder value

    # TORQUE COIL ERRORS
    TORQUE_COIL_OVERCURRENT_EVENT = const(0xB0)  # placeholder value
    TORQUE_COIL_OVERVOLTAGE_EVENT = const(0xB5)  # placeholder value
    TORQUE_COIL_UNDERVOLTAGE_LOCKOUT = const(0xB1)  # placeholder value
    TORQUE_COIL_THERMAL_SHUTDOWN = const(0xB2)  # placeholder value
    TORQUE_COIL_EXTENDED_CURRENT_LIMIT_EVENT = const(0xB3)  # placeholder value
    TORQUE_COIL_THROTTLE_OUTSIDE_RANGE = const(0xB4)  # placeholder value
    TORQUE_COIL_STALL_EVENT = const(0xB6)  # placeholder value

    # LIGHT SENSOR ERRORS
    LIGHT_SENSOR_HIGHER_THAN_THRESHOLD = const(0xC0)  # placeholder value
    LIGHT_SENSOR_LOWER_THAN_THRESHOLD = const(0xC1)  # placeholder value
    LIGHT_SENSOR_OVERFLOW = const(0xC2)  # placeholder value
    LIGHT_SENSOR_COVERSION_READY = const(0xC3)  # placeholder value

    # BOOST CHARGER ERRORS
    BOOST_CHARGER_CHARGE_SAFETY_EXPIRED = const(0xD0)  # placeholder value
    BOOST_CHARGER_BATT_OVP = const(0xD1)  # placeholder value
    BOOST_CHARGER_THERMAL_SHUTDOWN = const(0xD2)  # placeholder value
    BOOST_CHARGER_VBUS_OVP = const(0xD3)  # placeholder value
