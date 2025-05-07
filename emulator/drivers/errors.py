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
    LOG_DATA_ERROR = const(0x8)
    FN_CALL_ERROR = const(0x9)

    # IMU Errors
    IMU_ERROR_CODE = const(0xA)
    IMU_DROP_COMMAND_ERROR = const(0xB)
    IMU_FATAL_ERROR = const(0xC)

    # RTC Errors
    RTC_LOST_POWER = const(0xD)
    RTC_BATTERY_LOW = const(0xE)

    # GPS Errors
    GPS_UPDATE_CHECK_FAILED = const(0xF)

    # Radio Errors
    RADIO_RC64K_CALIBRATION_FAILED = const(0x10)
    RADIO_RC13M_CALIBRATION_FAILED = const(0x11)
    RADIO_PLL_CALIBRATION_FAILED = const(0x12)
    RADIO_ADC_CALIBRATION_FAILED = const(0x13)
    RADIO_IMG_CALIBRATION_FAILED = const(0x14)
    RADIO_XOSC_START_FAILED = const(0x15)
    RADIO_PA_RAMPING_FAILED = const(0x16)

    # Power Monitor Errors
    PWR_MON_ADC_ALERT_OVERCURRENT = const(0x17)

    # Torque Coil Errors
    TORQUE_COIL_OVERCURRENT_EVENT = const(0x18)
    TORQUE_COIL_OVERVOLTAGE_EVENT = const(0x19)
    TORQUE_COIL_UNDERVOLTAGE_LOCKOUT = const(0x1A)
    TORQUE_COIL_THERMAL_SHUTDOWN = const(0x1B)
    TORQUE_COIL_EXTENDED_CURRENT_LIMIT_EVENT = const(0x1C)
    TORQUE_COIL_THROTTLE_OUTSIDE_RANGE = const(0x1D)
    TORQUE_COIL_STALL_EVENT = const(0x1E)

    # Light Sensor Errors
    LIGHT_SENSOR_HIGHER_THAN_THRESHOLD = const(0x1F)
    LIGHT_SENSOR_LOWER_THAN_THRESHOLD = const(0x20)
    LIGHT_SENSOR_OVERFLOW = const(0x21)

    # Boost Charger Errors
    BOOST_CHARGER_CHARGE_SAFETY_EXPIRED = const(0x22)
    BOOST_CHARGER_BATT_OVP = const(0x23)
    BOOST_CHARGER_THERMAL_SHUTDOWN = const(0x24)
    BOOST_CHARGER_VBUS_OVP = const(0x25)

    # Battery Heater Errors
    BATT_HEATER_EN_GPIO_ERROR = const(0x26)
    BATT_HEATER_HEAT0_GPIO_ERROR = const(0x27)
    BATT_HEATER_HEAT1_GPIO_ERROR = const(0x28)

    # Watchdog Errors
    WATCHDOG_EN_GPIO_ERROR = const(0x29)
    WATCHDOG_INPUT_GPIO_ERROR = const(0x2A)
