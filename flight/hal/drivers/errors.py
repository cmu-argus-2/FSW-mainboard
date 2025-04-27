from micropython import const


class Errors:

    # Non-Device Specific Errors
    NO_ERROR = const(0x0)
    DEVICE_NOT_INITIALISED = const(0x1)

    # Error Handling
    INVALID_DEVICE_NAME = const(0x2)
    DEVICE_DEAD = const(0x3)
    REBOOT_DEVICE = const(0x4)
    NO_REBOOT = const(0x5)
    GRACEFUL_REBOOT = const(0x6)
    LOG_DATA = const(0x7)

    # IMU Errors
    IMU_ERROR_CODE = const(0x8)
    IMU_DROP_COMMAND_ERROR = const(0x9)
    IMU_FATAL_ERROR = const(0xA)

    # RTC Errors
    RTC_LOST_POWER = const(0x8)
    RTC_BATTERY_LOW = const(0x9)

    # GPS Errors
    GPS_UPDATE_CHECK_FAILED = const(0x8)

    # Radio Errors
    RADIO_RC64K_CALIBRATION_FAILED = const(0x8)
    RADIO_RC13M_CALIBRATION_FAILED = const(0x9)
    RADIO_PLL_CALIBRATION_FAILED = const(0xA)
    RADIO_ADC_CALIBRATION_FAILED = const(0xB)
    RADIO_IMG_CALIBRATION_FAILED = const(0xC)
    RADIO_XOSC_START_FAILED = const(0xD)
    RADIO_PA_RAMPING_FAILED = const(0xE)

    # Power Monitor Errors
    PWR_MON_ADC_ALERT_OVERCURRENT = const(0x8)

    # Torque Coil Errors
    TORQUE_COIL_OVERCURRENT_EVENT = const(0x8)
    TORQUE_COIL_OVERVOLTAGE_EVENT = const(0x9)
    TORQUE_COIL_UNDERVOLTAGE_LOCKOUT = const(0xA)
    TORQUE_COIL_THERMAL_SHUTDOWN = const(0xB)
    TORQUE_COIL_EXTENDED_CURRENT_LIMIT_EVENT = const(0xC)
    TORQUE_COIL_THROTTLE_OUTSIDE_RANGE = const(0xD)
    TORQUE_COIL_STALL_EVENT = const(0xE)

    # Light Sensor Errors
    LIGHT_SENSOR_HIGHER_THAN_THRESHOLD = const(0x8)
    LIGHT_SENSOR_LOWER_THAN_THRESHOLD = const(0x9)
    LIGHT_SENSOR_OVERFLOW = const(0xA)
    LIGHT_SENSOR_COVERSION_READY = const(0xB)

    # Boost Charger Errors
    BOOST_CHARGER_CHARGE_SAFETY_EXPIRED = const(0x8)
    BOOST_CHARGER_BATT_OVP = const(0x9)
    BOOST_CHARGER_THERMAL_SHUTDOWN = const(0xA)
    BOOST_CHARGER_VBUS_OVP = const(0xB)
