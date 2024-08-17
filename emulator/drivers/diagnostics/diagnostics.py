"""
diagnostics.py

This file contains the base class for all components which need diagnostic tests run

Author: Harry Rosmann
"""

import time


class Diagnostics:
    """
    Interface for all component diagnostic tests
    """

    ############### ERROR CODES ###############
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

    # Neopixel errors
    NEOPIXEL_NOT_INITIALIZED = 38

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
    DIAGNOSTICS_ERROR_LIGHT_SENSOR_ZM = 55
    # DIAGNOSTICS_ERROR_LIGHT_SENSOR_ZM = 56
    DIAGNOSTICS_ERROR_RTC = 57
    DIAGNOSTICS_ERROR_RADIO = 58
    DIAGNOSTICS_ERROR_NEOPIXEL = 59
    DIAGNOSTICS_ERROR_BURN_WIRES = 60
    DIAGNOSTICS_ERROR_UNKNOWN = 61

    VFS_NOT_INITIALIZED = 62

    __ERROR_MIN = 0
    __ERROR_MAX = 62

    RESET_DELAY = 0.01

    def __init__(self, enable) -> None:
        self._enable = enable
        self.errors_present = False

    def error_present(self) -> bool:
        return self.errors_present

    def run_diagnostics(self) -> list:
        """run_diagnostic_test: Run all tests for the component"""
        raise NotImplementedError("Subclasses must implement run_diagnostic_test method")

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

    @staticmethod
    def convert_errors_to_byte_array(errors: list) -> bytes:
        """convert_errors_to_byte_array: Convert a list of errors to a packed set of bytes.
        Each bit represents a corresponding error.

        :param errors: The list of errors. Must be a valid diagnostic error
        :returns: The byte array of toggled error bits
        """
        BITS_IN_BYTE = 8

        num_bytes = Diagnostics.__ERROR_MAX / BITS_IN_BYTE
        error_bytes = bytearray([0x00] * num_bytes)

        unique_errors = list(set(errors))

        for error in unique_errors:
            # Ensure it is a valid error number
            if error < Diagnostics.__ERROR_MIN or error > Diagnostics.__ERROR_MAX:
                raise RuntimeError(f"Unrecognized error number ({error})")

            # NOTE: We DO want to track if there is no error

            byte_num = error / BITS_IN_BYTE

            error_bytes[byte_num] |= 0x1 << error

        return error_bytes

    # @staticmethod
    # def diagnostic_to_string(error: int) -> str:
    #     """diagnostic_to_string: Convert a diagnostic error to a string

    #     :param error: The error code
    #     :returns: The string representation of the error
    #     """
    #     if error == Diagnostics.NOERROR:
    #         return "No error"
    #     elif error == Diagnostics.ADM1176_NOT_INITIALIZED:
    #         return "ADM1176 not initialized"
    #     elif error == Diagnostics.ADM1176_NOT_CONNECTED_TO_POWER:
    #         return "ADM1176 not connected to power"
    #     elif error == Diagnostics.ADM1176_VOLTAGE_OUT_OF_RANGE:
    #         return "ADM1176 voltage out of range"
    #     elif error == Diagnostics.ADM1176_COULD_NOT_TURN_ON:
    #         return "ADM1176 could not turn on"
    #     elif error == Diagnostics.ADM1176_COULD_NOT_TURN_OFF:
    #         return "ADM1176 could not turn off"
    #     elif error == Diagnostics.ADM1176_ADC_OC_OVERCURRENT_MAX:
    #         return "ADM1176 ADC overcurrent max"
    #     elif error == Diagnostics.ADM1176_ADC_ALERT_OVERCURRENT_MAX:
    #         return "ADM1176 ADC alert overcurrent max"
    #     elif error == Diagnostics.ADM1176_ADC_OC_OVERCURRENT_MIN_THRESHOLD:
    #         return "ADM1176 ADC overcurrent min threshold"
    #     elif error == Diagnostics.ADM1176_ADC_ALERT_OVERCURRENT_MIN_THRESHOLD:
    #         return "ADM1176 ADC alert overcurrent min threshold"
    #     elif error == Diagnostics.BQ25883_NOT_INITIALIZED:
    #         return "BQ25883 not initialized"
    #     elif error == Diagnostics.BQ25883_INPUT_OVERVOLTAGE:
    #         return "BQ25883 input overvoltage"
    #     elif error == Diagnostics.BQ25883_THERMAL_SHUTDOWN:
    #         return "BQ25883 thermal shutdown"
    #     elif error == Diagnostics.BQ25883_BATTERY_OVERVOLTAGE:
    #         return "BQ25883 battery overvoltage"
    #     elif error == Diagnostics.BQ25883_CHARGE_SAFETY_TIMER_EXPIRED:
    #         return "BQ25883 charge safety timer expired"
    #     elif error == Diagnostics.OPT4001_NOT_INITIALIZED:
    #         return "OPT4001 not initialized"
    #     elif error == Diagnostics.OPT4001_CRC_COUNTER_TEST_FAILED:
    #         return "OPT4001 CRC counter test failed"
    #     elif error == Diagnostics.OPT4001_CRC_COUNTER_TEST_FAILED:
    #         return "OPT4001 ID check failed"
    #     elif error == Diagnostics.GPS_NOT_INITIALIZED:
    #         return "GPS not initialized"
    #     elif error == Diagnostics.GPS_UPDATE_CHECK_FAILED:
    #         return "GPS update check failed"
    #     elif error == Diagnostics.PCF8523_NOT_INITIALIZED:
    #         return "PCF8523 not initialized"
    #     elif error == Diagnostics.PCF8523_BATTERY_LOW:
    #         return "PCF8523 battery low"
    #     elif error == Diagnostics.PCF8523_LOST_POWER:
    #         return "PCF8523 lost power"
    #     elif error == Diagnostics.BMX160_NOT_INITIALIZED:
    #         return "BMX160 not initialized"
    #     elif error == Diagnostics.BMX160_FATAL_ERROR:
    #         return "BMX160 fatal error"
    #     elif error == Diagnostics.BMX160_NON_FATAL_ERROR:
    #         return "BMX160 non-fatal error"
    #     elif error == Diagnostics.BMX160_DROP_COMMAND_ERROR:
    #         return "BMX160 drop command error"
    #     elif error == Diagnostics.BMX160_UNSPECIFIED_ERROR:
    #         return "BMX160 unspecified error"
    #     elif error == Diagnostics.DRV8830_NOT_INITIALIZED:
    #         return "DRV8830 not initialized"
    #     elif error == Diagnostics.DRV8830_OVERCURRENT_EVENT:
    #         return "DRV8830 overcurrent event"
    #     elif error == Diagnostics.DRV8830_UNDERVOLTAGE_LOCKOUT:
    #         return "DRV8830 undervoltage lockout"
    #     elif error == Diagnostics.DRV8830_OVERTEMPERATURE_CONDITION:
    #         return "DRV8830 overtemperature condition"
    #     elif error == Diagnostics.DRV8830_EXTENDED_CURRENT_LIMIT_EVENT:
    #         return "DRV8830 extended current limit event"
    #     elif error == Diagnostics.DRV8830_THROTTLE_OUTSIDE_RANGE:
    #         return "DRV8830 throttle outside range"
    #     elif error == Diagnostics.DRV8830_THROTTLE_VOLTS_OUTSIDE_RANGE:
    #         return "DRV8830 throttle volts outside range"
    #     elif error == Diagnostics.DRV8830_THROTTLE_RAW_OUTSIDE_RANGE:
    #         return "DRV8830 throttle raw outside range"
    #     elif error == Diagnostics.RFM9X_NOT_INITIALIZED:
    #         return "RFM9X not initialized"
    #     elif error == Diagnostics.SDCARD_NOT_INITIALIZED:
    #         return "SD card not initialized"
    #     elif error == Diagnostics.NEOPIXEL_NOT_INITIALIZED:
    #         return "Neopixel not initialized"
    #     elif error == Diagnostics.BURNWIRES_NOT_INITIALIZED:
    #         return "Burn wires not initialized"
    #     elif error == Diagnostics.DIAGNOSTICS_ERROR_GPS:
    #         return "Diagnostics error: GPS"
    #     elif error == Diagnostics.DIAGNOSTICS_ERROR_BATTERY_POWER_MONITOR:
    #         return "Diagnostics error: Battery power monitor"
    #     elif error == Diagnostics.DIAGNOSTICS_ERROR_JETSON_POWER_MONITOR:
    #         return "Diagnostics error: Jetson power monitor"
    #     elif error == Diagnostics.DIAGNOSTICS_ERROR_IMU:
    #         return "Diagnostics error: IMU"
    #     elif error == Diagnostics.DIAGNOSTICS_ERROR_CHARGER:
    #         return "Diagnostics error: Charger"
    #     elif error == Diagnostics.DIAGNOSTICS_ERROR_TORQUE_XP:
    #         return "Diagnostics error: Torque XP"
    #     elif error == Diagnostics.DIAGNOSTICS_ERROR_TORQUE_XM:
    #         return "Diagnostics error: Torque XM"
    #     elif error == Diagnostics.DIAGNOSTICS_ERROR_TORQUE_YP:
    #         return "Diagnostics error: Torque YP"
    #     elif error == Diagnostics.DIAGNOSTICS_ERROR_TORQUE_YM:
    #         return "Diagnostics error: Torque YM"
    #     elif error == Diagnostics.DIAGNOSTICS_ERROR_TORQUE_Z:
    #         return "Diagnostics error: Torque Z"
    #     elif error == Diagnostics.DIAGNOSTICS_ERROR_LIGHT_SENSOR_XP:
    #         return "Diagnostics error: Sun sensor XP"
    #     elif error == Diagnostics.DIAGNOSTICS_ERROR_LIGHT_SENSOR_XM:
    #         return "Diagnostics error: Sun sensor XM"
    #     elif error == Diagnostics.DIAGNOSTICS_ERROR_LIGHT_SENSOR_YP:
    #         return "Diagnostics error: Sun sensor YP"
    #     elif error == Diagnostics.DIAGNOSTICS_ERROR_LIGHT_SENSOR_YM:
    #         return "Diagnostics error: Sun sensor YM"
    #     elif error == Diagnostics.DIAGNOSTICS_ERROR_LIGHT_SENSOR_ZP:
    #         return "Diagnostics error: Sun sensor ZP"
    #     elif error == Diagnostics.DIAGNOSTICS_ERROR_LIGHT_SENSOR_ZM:
    #         return "Diagnostics error: Sun sensor ZM"
    #     elif error == Diagnostics.DIAGNOSTICS_ERROR_RTC:
    #         return "Diagnostics error: RTC"
    #     elif error == Diagnostics.DIAGNOSTICS_ERROR_RADIO:
    #         return "Diagnostics error: Radio"
    #     elif error == Diagnostics.DIAGNOSTICS_ERROR_NEOPIXEL:
    #         return "Diagnostics error: Neopixel"
    #     elif error == Diagnostics.DIAGNOSTICS_ERROR_BURN_WIRES:
    #         return "Diagnostics error: Burn wires"
    #     elif error == Diagnostics.DIAGNOSTICS_ERROR_UNKNOWN:
    #         return "Diagnostics error: Unknown"
    #     elif error == Diagnostics.JETSON_COMM_NOT_INITIALIZED:
    #         return "Jetson comm not initialized"
    #     else:
    #         return "Unknown error code"
