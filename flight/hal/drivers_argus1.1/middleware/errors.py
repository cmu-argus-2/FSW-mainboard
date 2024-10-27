from micropython import const


class Errors:
    """
    Interface for all component diagnostic tests
    """

    ############### ERROR CODES ###############
    NOERROR = const(0)

    # ADM1176 errors
    ADM1176_NOT_INITIALIZED = const(1)
    ADM1176_NOT_CONNECTED_TO_POWER = const(2)
    ADM1176_VOLTAGE_OUT_OF_RANGE = const(3)
    ADM1176_COULD_NOT_TURN_ON = const(4)
    ADM1176_COULD_NOT_TURN_OFF = const(5)
    ADM1176_ADC_OC_OVERCURRENT_MAX = const(6)
    ADM1176_ADC_ALERT_OVERCURRENT_MAX = const(7)
    ADM1176_ADC_OC_OVERCURRENT_MIN_THRESHOLD = const(8)
    ADM1176_ADC_ALERT_OVERCURRENT_MIN_THRESHOLD = const(9)

    # BQ25883 errors
    BQ25883_NOT_INITIALIZED = const(10)
    BQ25883_INPUT_OVERVOLTAGE = const(11)
    BQ25883_THERMAL_SHUTDOWN = const(12)
    BQ25883_BATTERY_OVERVOLTAGE = const(13)
    BQ25883_CHARGE_SAFETY_TIMER_EXPIRED = const(14)

    # OPT4001 errors
    OPT4001_NOT_INITIALIZED = const(15)
    OPT4001_CRC_COUNTER_TEST_FAILED = const(16)
    OPT4001_ID_CHECK_FAILED = const(17)

    # Adafruit GPS errors
    GPS_NOT_INITIALIZED = const(18)
    GPS_UPDATE_CHECK_FAILED = const(19)

    # PCF8523 errors
    PCF8523_NOT_INITIALIZED = const(20)
    PCF8523_BATTERY_LOW = const(21)
    PCF8523_LOST_POWER = const(22)

    # BMX160 errors
    BMX160_NOT_INITIALIZED = const(23)
    BMX160_FATAL_ERROR = const(24)
    BMX160_NON_FATAL_ERROR = const(25)
    BMX160_DROP_COMMAND_ERROR = const(26)
    BMX160_UNSPECIFIED_ERROR = const(27)

    # DRV8830 errors
    DRV8830_NOT_INITIALIZED = const(28)
    DRV8830_OVERCURRENT_EVENT = const(29)
    DRV8830_UNDERVOLTAGE_LOCKOUT = const(30)
    DRV8830_OVERTEMPERATURE_CONDITION = const(31)
    DRV8830_EXTENDED_CURRENT_LIMIT_EVENT = const(32)
    DRV8830_THROTTLE_OUTSIDE_RANGE = const(33)
    DRV8830_THROTTLE_VOLTS_OUTSIDE_RANGE = const(34)
    DRV8830_THROTTLE_RAW_OUTSIDE_RANGE = const(35)

    # RFM9X errors
    RFM9X_NOT_INITIALIZED = const(36)

    # SD card errors
    SDCARD_NOT_INITIALIZED = const(37)

    # Neopixel errors
    NEOPIXEL_NOT_INITIALIZED = const(38)

    # Burn Wire errors
    BURNWIRES_NOT_INITIALIZED = const(39)

    # Jetson Comm
    JETSON_COMM_NOT_INITIALIZED = const(40)

    # Diagnostics errors - occur when running diagnostics on the system fails
    DIAGNOSTICS_ERROR_GPS = const(41)
    DIAGNOSTICS_ERROR_BATTERY_POWER_MONITOR = const(42)
    DIAGNOSTICS_ERROR_JETSON_POWER_MONITOR = const(43)
    DIAGNOSTICS_ERROR_IMU = const(44)
    DIAGNOSTICS_ERROR_CHARGER = const(45)
    DIAGNOSTICS_ERROR_TORQUE_XP = const(46)
    DIAGNOSTICS_ERROR_TORQUE_XM = const(47)
    DIAGNOSTICS_ERROR_TORQUE_YP = const(48)
    DIAGNOSTICS_ERROR_TORQUE_YM = const(49)
    DIAGNOSTICS_ERROR_TORQUE_Z = const(50)
    DIAGNOSTICS_ERROR_SUN_SENSOR_XP = const(51)
    DIAGNOSTICS_ERROR_SUN_SENSOR_XM = const(52)
    DIAGNOSTICS_ERROR_SUN_SENSOR_YP = const(53)
    DIAGNOSTICS_ERROR_SUN_SENSOR_YM = const(54)
    DIAGNOSTICS_ERROR_SUN_SENSOR_ZM = const(55)
    DIAGNOSTICS_ERROR_RTC = const(57)
    DIAGNOSTICS_ERROR_RADIO = const(58)
    DIAGNOSTICS_ERROR_NEOPIXEL = const(59)
    DIAGNOSTICS_ERROR_BURN_WIRES = const(60)
    DIAGNOSTICS_ERROR_UNKNOWN = const(61)

    VFS_NOT_INITIALIZED = const(62)

    __ERROR_MIN = const(0)
    __ERROR_MAX = const(62)

    RESET_DELAY = 0.01

    errors = {
        NOERROR: "no error",
        ADM1176_NOT_INITIALIZED: "ADM1176 not initialized",
        ADM1176_NOT_CONNECTED_TO_POWER: "ADM1176 not connected to power",
        ADM1176_VOLTAGE_OUT_OF_RANGE: "ADM1176 voltage out of range",
        ADM1176_COULD_NOT_TURN_ON: "ADM1176 could not turn on",
        ADM1176_COULD_NOT_TURN_OFF: "ADM1176 could not turn off",
        ADM1176_ADC_OC_OVERCURRENT_MAX: "ADM1176 ADC OC overcurrent max",
        ADM1176_ADC_ALERT_OVERCURRENT_MAX: "ADM1176 ADC alert overcurrent max",
        ADM1176_ADC_OC_OVERCURRENT_MIN_THRESHOLD: "ADM1176 ADC OC overcurrent min threshold",
        ADM1176_ADC_ALERT_OVERCURRENT_MIN_THRESHOLD: "ADM1176 alert overcurrent min threshold",
        BQ25883_NOT_INITIALIZED: "BQ25883 not initialized",
        BQ25883_INPUT_OVERVOLTAGE: "BQ25883 input overvoltage",
        BQ25883_THERMAL_SHUTDOWN: "BQ25883 thermal shutdown",
        BQ25883_BATTERY_OVERVOLTAGE: "BQ25883 battery overvoltage",
        BQ25883_CHARGE_SAFETY_TIMER_EXPIRED: "BQ25883 charge safety timer expired",
        OPT4001_NOT_INITIALIZED: "OPT4001 not initialized",
        OPT4001_CRC_COUNTER_TEST_FAILED: "OPT4001 crc ounter test failed",
        OPT4001_ID_CHECK_FAILED: "OPT4001 id check failed",
        GPS_NOT_INITIALIZED: "GPS not initialized",
        GPS_UPDATE_CHECK_FAILED: "GPS update check failed",
        PCF8523_NOT_INITIALIZED: "PCF8523 not initialized",
        PCF8523_BATTERY_LOW: "PCF8523 battery low",
        PCF8523_LOST_POWER: "PCF8523 lost power",
        BMX160_NOT_INITIALIZED: "BMX160 not initialized",
        BMX160_FATAL_ERROR: "BMX160 fatal error",
        BMX160_NON_FATAL_ERROR: "BMX160 non fatal error",
        BMX160_DROP_COMMAND_ERROR: "BMX160 drop command error",
        BMX160_UNSPECIFIED_ERROR: "BMX160 unspecified error",
        DRV8830_NOT_INITIALIZED: "DRV8830 not initialized",
        DRV8830_OVERCURRENT_EVENT: "DRV8830 overcurrent event",
        DRV8830_UNDERVOLTAGE_LOCKOUT: "DRV8830 undervoltage lockout",
        DRV8830_OVERTEMPERATURE_CONDITION: "DRV8830 overtemperature condition",
        DRV8830_EXTENDED_CURRENT_LIMIT_EVENT: "DRV8830 extended current limit event",
        DRV8830_THROTTLE_OUTSIDE_RANGE: "DRV8830 throttle outside range",
        DRV8830_THROTTLE_VOLTS_OUTSIDE_RANGE: "DRV8830 throttle volts range",
        DRV8830_THROTTLE_RAW_OUTSIDE_RANGE: "DRV8830 throttle raw outside range",
        RFM9X_NOT_INITIALIZED: "RFM9x not initialized",
        SDCARD_NOT_INITIALIZED: "SD card not initialized",
        NEOPIXEL_NOT_INITIALIZED: "neopixel not initialized",
        BURNWIRES_NOT_INITIALIZED: "burnwires not initialized",
        JETSON_COMM_NOT_INITIALIZED: "jetson comms not initialized",
        VFS_NOT_INITIALIZED: "virtual file system not initialized",
        DIAGNOSTICS_ERROR_GPS: "GPS error",
        DIAGNOSTICS_ERROR_BATTERY_POWER_MONITOR: "battery power monitor error",
        DIAGNOSTICS_ERROR_JETSON_POWER_MONITOR: "jetson power monitor error",
        DIAGNOSTICS_ERROR_IMU: "imu error",
        DIAGNOSTICS_ERROR_CHARGER: "charger error",
        DIAGNOSTICS_ERROR_TORQUE_XP: "torque xp error",
        DIAGNOSTICS_ERROR_TORQUE_XM: "torque xm error",
        DIAGNOSTICS_ERROR_TORQUE_YP: "torque yp error",
        DIAGNOSTICS_ERROR_TORQUE_YM: "torque ym error",
        DIAGNOSTICS_ERROR_TORQUE_Z: "torque z error",
        DIAGNOSTICS_ERROR_SUN_SENSOR_XP: "light sensor xp error",
        DIAGNOSTICS_ERROR_SUN_SENSOR_XM: "light sensor xm error",
        DIAGNOSTICS_ERROR_SUN_SENSOR_YP: "light sensor yp error",
        DIAGNOSTICS_ERROR_SUN_SENSOR_YM: "light sensor ym error",
        DIAGNOSTICS_ERROR_SUN_SENSOR_ZM: "light sensor zm error",
        DIAGNOSTICS_ERROR_RTC: "rtc error",
        DIAGNOSTICS_ERROR_RADIO: "radio error",
        DIAGNOSTICS_ERROR_NEOPIXEL: "neopixel error",
        DIAGNOSTICS_ERROR_BURN_WIRES: "brunwires error",
        DIAGNOSTICS_ERROR_UNKNOWN: "unknown error",
    }

    def diagnostic_to_string(self, error):
        return self.errors[error]
