import time

FAULT_HANDLE_RETRIES = 3


class driver_cant_handle_exception(Exception):
    """
    to be used when the handler attempts to handle a method that wasn't given to it
    as a handlable method
    """

    def __init__(self, exception: Exception):
        self.exception = exception
        super().__init__()

    def __str__(self):
        return f"{type(self.exception).__name__}: {self.exception}"


class ErrorCodes:
    NOERROR = 0

    # ADM1176 errors
    ADM1176_NOT_INITIALIZED = 1
    ADM1176_NOT_CONNECTED_TO_POWER = 2
    ADM1176_VOLTAGE_OUT_OF_RANGE = 3
    ADM1176_COULD_NOT_TURN_ON = 4
    ADM1176_COULD_NOT_TURN_OFF = 5
    ADM1176_ADC_OC_OVERCURRENT_MAX = 6
    ADM1176_ADC_ALERT_OVERCURRENT_MAX = 7
    ADM1176_ADC_OC_OVERCURRENT_MIN_THRESHOLD = 8
    ADM1176_ADC_ALERT_OVERCURRENT_MIN_THRESHOLD = 9

    # BQ25883 errors
    BQ25883_NOT_INITIALIZED = 10
    BQ25883_INPUT_OVERVOLTAGE = 11
    BQ25883_THERMAL_SHUTDOWN = 12
    BQ25883_BATTERY_OVERVOLTAGE = 13
    BQ25883_CHARGE_SAFETY_TIMER_EXPIRED = 14

    # OPT4001 errors
    OPT4001_NOT_INITIALIZED = 15
    OPT4001_CRC_COUNTER_TEST_FAILED = 16
    OPT4001_ID_CHECK_FAILED = 17

    # Adafruit GPS errors
    GPS_NOT_INITIALIZED = 18
    GPS_UPDATE_CHECK_FAILED = 19

    # PCF8523 errors
    PCF8523_NOT_INITIALIZED = 20
    PCF8523_BATTERY_LOW = 21
    PCF8523_LOST_POWER = 22

    # BMX160 errors
    BMX160_NOT_INITIALIZED = 23
    BMX160_FATAL_ERROR = 24
    BMX160_NON_FATAL_ERROR = 25
    BMX160_DROP_COMMAND_ERROR = 26
    BMX160_UNSPECIFIED_ERROR = 27

    # DRV8830 errors
    DRV8830_NOT_INITIALIZED = 28
    DRV8830_OVERCURRENT_EVENT = 29
    DRV8830_UNDERVOLTAGE_LOCKOUT = 30
    DRV8830_OVERTEMPERATURE_CONDITION = 31
    DRV8830_EXTENDED_CURRENT_LIMIT_EVENT = 32
    DRV8830_THROTTLE_OUTSIDE_RANGE = 33
    DRV8830_THROTTLE_VOLTS_OUTSIDE_RANGE = 34
    DRV8830_THROTTLE_RAW_OUTSIDE_RANGE = 35

    # RFM9X errors
    RFM9X_NOT_INITIALIZED = 36

    # SD card errors
    SDCARD_NOT_INITIALIZED = 37

    # Burn Wire errors
    BURNWIRES_NOT_INITIALIZED = 39

    # Jetson Comm
    JETSON_COMM_NOT_INITIALIZED = 40

    # Diagnostics errors - occur when running diagnostics on the system fails
    DIAGNOSTICS_ERROR_GPS = 41
    DIAGNOSTICS_ERROR_BATTERY_POWER_MONITOR = 42
    DIAGNOSTICS_ERROR_JETSON_POWER_MONITOR = 43
    DIAGNOSTICS_ERROR_IMU = 44
    DIAGNOSTICS_ERROR_CHARGER = 45
    DIAGNOSTICS_ERROR_TORQUE_XP = 46
    DIAGNOSTICS_ERROR_TORQUE_XM = 47
    DIAGNOSTICS_ERROR_TORQUE_YP = 48
    DIAGNOSTICS_ERROR_TORQUE_YM = 49
    DIAGNOSTICS_ERROR_TORQUE_Z = 50
    DIAGNOSTICS_ERROR_LIGHT_SENSOR_XP = 51
    DIAGNOSTICS_ERROR_LIGHT_SENSOR_XM = 52
    DIAGNOSTICS_ERROR_LIGHT_SENSOR_YP = 53
    DIAGNOSTICS_ERROR_LIGHT_SENSOR_YM = 54
    DIAGNOSTICS_ERROR_LIGHT_SENSOR_ZP = 55
    # DIAGNOSTICS_ERROR_LIGHT_SENSOR_ZM = 56
    DIAGNOSTICS_ERROR_RTC = 57
    DIAGNOSTICS_ERROR_RADIO = 58
    DIAGNOSTICS_ERROR_BURN_WIRES = 60
    DIAGNOSTICS_ERROR_UNKNOWN = 61

    VFS_NOT_INITIALIZED = 62

    __ERROR_MIN = 0
    __ERROR_MAX = 62

    RESET_DELAY = 0.01


class Driver:
    # set of strings containing method names
    # dict of method name to checker function and method-specific exception to give to middlware

    RESET_DELAY = 0.01

    def __init__(self, enable=None) -> None:
        self.handleable = {}
        self.checkers = {}
        self._enable = enable
        self.errors_present = False

    def handler(self, method):
        if method.__name__ not in self.handleable:
            raise driver_cant_handle_exception("tried to handle unhandleable method")
        checker, m_exception = self.handleable[method.__name__]

        def handle(*args, **kwargs):
            try:
                res = method(*args, **kwargs)
                flags = self.get_flags()
                if checker(res, flags):
                    return res
                else:
                    raise m_exception(f"erroneus result: {res}")
            except Exception:
                flags = self.get_flags()
                for flag in flags:
                    fixer = flags[flag]
                    if fixer is not None:
                        fixer()
                try:
                    if val := self.retry(method, *args, **kwargs):
                        flags = self.get_flags()
                        if checker(val, flags):
                            return val
                        else:
                            raise m_exception("erroneus result")
                    else:
                        raise m_exception("couldn't retry")
                except Exception as e:
                    raise m_exception(e)

        return handle

    def get_flags(self) -> dict:
        """
        should return a dictionary of (raised flag -> fixer function)
        or if flag cannot be fixed in software (raised flag -> None)
        """
        raise NotImplementedError

    def retry(self, method, *args, **kwargs) -> bool:
        """handle_fault: Handle the exception generated by the fault.

        :returns: True the value requested, otherwise raises exception
        """

        tries = 0
        while tries < FAULT_HANDLE_RETRIES:
            try:
                if self.resetable:
                    self.reset()
                else:
                    value = method(*args, **kwargs)  # Run the method again
                return value
            except Exception:
                tries += 1
        return None  # Fault could not be handled after retries

    @property
    def resetable(self):
        """resetable: Check if the component is resetable"""
        return self._enable is not None

    def reset(self) -> None:
        """reset: Reset the component by quickly turning off and on"""
        if self._enable is not None:
            self._enable.value = False
            time.sleep(self.RESET_DELAY)
            self._enable.value = True

    def enable(self):
        """enable: Enable the component"""
        if self._enable is not None:
            self._enable.value = True

    def disable(self):
        """disable: Disable the component"""
        if self._enable is not None:
            self._enable.value = False

    def run_diagnostics(self) -> list:
        """run_diagnostic_test: Run all tests for the component"""
        raise NotImplementedError("Subclasses must implement run_diagnostic_test method")
