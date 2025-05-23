# Index constants for accessing data in the Data Handler

from micropython import const


class CDH_IDX:
    TIME = const(0)
    SC_STATE = const(1)
    SD_USAGE = const(2)
    CURRENT_RAM_USAGE = const(3)
    REBOOT_COUNT = const(4)
    WATCHDOG_TIMER = const(5)
    HAL_BITFLAGS = const(6)
    DETUMBLING_ERROR_FLAG = const(7)


class EPS_IDX:
    TIME_EPS = const(0)
    EPS_POWER_FLAG = const(1)
    MAINBOARD_TEMPERATURE = const(2)
    MAINBOARD_VOLTAGE = const(3)
    MAINBOARD_CURRENT = const(4)
    BATTERY_PACK_TEMPERATURE = const(5)
    BATTERY_PACK_REPORTED_SOC = const(6)
    BATTERY_PACK_REPORTED_CAPACITY = const(7)
    BATTERY_PACK_CURRENT = const(8)
    BATTERY_PACK_VOLTAGE = const(9)
    BATTERY_PACK_MIDPOINT_VOLTAGE = const(10)
    BATTERY_PACK_TTE = const(11)
    BATTERY_PACK_TTF = const(12)
    XP_COIL_VOLTAGE = const(13)
    XP_COIL_CURRENT = const(14)
    XM_COIL_VOLTAGE = const(15)
    XM_COIL_CURRENT = const(16)
    YP_COIL_VOLTAGE = const(17)
    YP_COIL_CURRENT = const(18)
    YM_COIL_VOLTAGE = const(19)
    YM_COIL_CURRENT = const(20)
    ZP_COIL_VOLTAGE = const(21)
    ZP_COIL_CURRENT = const(22)
    ZM_COIL_VOLTAGE = const(23)
    ZM_COIL_CURRENT = const(24)
    JETSON_INPUT_VOLTAGE = const(25)
    JETSON_INPUT_CURRENT = const(26)
    RF_LDO_OUTPUT_VOLTAGE = const(27)
    RF_LDO_OUTPUT_CURRENT = const(28)
    GPS_VOLTAGE = const(29)
    GPS_CURRENT = const(30)
    XP_SOLAR_CHARGE_VOLTAGE = const(31)
    XP_SOLAR_CHARGE_CURRENT = const(32)
    XM_SOLAR_CHARGE_VOLTAGE = const(33)
    XM_SOLAR_CHARGE_CURRENT = const(34)
    YP_SOLAR_CHARGE_VOLTAGE = const(35)
    YP_SOLAR_CHARGE_CURRENT = const(36)
    YM_SOLAR_CHARGE_VOLTAGE = const(37)
    YM_SOLAR_CHARGE_CURRENT = const(38)
    ZP_SOLAR_CHARGE_VOLTAGE = const(39)
    ZP_SOLAR_CHARGE_CURRENT = const(40)
    ZM_SOLAR_CHARGE_VOLTAGE = const(41)
    ZM_SOLAR_CHARGE_CURRENT = const(42)
    BATTERY_HEATERS_ENABLED = const(43)


class EPS_WARNING_IDX:
    TIME_EPS_WARNING = const(0)
    MAINBOARD_POWER_ALERT = const(1)
    PERIPHERAL_POWER_ALERT = const(2)
    RADIO_POWER_ALERT = const(3)
    JETSON_POWER_ALERT = const(4)
    XP_COIL_POWER_ALERT = const(5)
    XM_COIL_POWER_ALERT = const(6)
    YP_COIL_POWER_ALERT = const(7)
    YM_COIL_POWER_ALERT = const(8)
    ZP_COIL_POWER_ALERT = const(9)
    ZM_COIL_POWER_ALERT = const(10)


class ADCS_IDX:
    TIME_ADCS = const(0)
    MODE = const(1)
    GYRO_X = const(2)
    GYRO_Y = const(3)
    GYRO_Z = const(4)
    MAG_X = const(5)
    MAG_Y = const(6)
    MAG_Z = const(7)
    SUN_STATUS = const(8)
    SUN_VEC_X = const(9)
    SUN_VEC_Y = const(10)
    SUN_VEC_Z = const(11)
    LIGHT_SENSOR_XP = const(12)
    LIGHT_SENSOR_XM = const(13)
    LIGHT_SENSOR_YP = const(14)
    LIGHT_SENSOR_YM = const(15)
    LIGHT_SENSOR_ZP1 = const(16)
    LIGHT_SENSOR_ZP2 = const(17)
    LIGHT_SENSOR_ZP3 = const(18)
    LIGHT_SENSOR_ZP4 = const(19)
    LIGHT_SENSOR_ZM = const(20)
    XP_COIL_STATUS = const(21)
    XM_COIL_STATUS = const(22)
    YP_COIL_STATUS = const(23)
    YM_COIL_STATUS = const(24)
    ZP_COIL_STATUS = const(25)
    ZM_COIL_STATUS = const(26)
    ATTITUDE_QW = const(27)
    ATTITUDE_QX = const(28)
    ATTITUDE_QY = const(29)
    ATTITUDE_QZ = const(30)


class IMU_IDX:
    TIME_IMU = const(0)
    ACCEL_X = const(1)
    ACCEL_Y = const(2)
    ACCEL_Z = const(3)
    MAGNETOMETER_X = const(4)
    MAGNETOMETER_Y = const(5)
    MAGNETOMETER_Z = const(6)
    GYROSCOPE_X = const(7)
    GYROSCOPE_Y = const(8)
    GYROSCOPE_Z = const(9)


class GPS_IDX:
    TIME_GPS = const(0)
    GPS_MESSAGE_ID = const(1)
    GPS_FIX_MODE = const(2)
    GPS_NUMBER_OF_SV = const(3)
    GPS_GNSS_WEEK = const(4)
    GPS_GNSS_TOW = const(5)
    GPS_LATITUDE = const(6)
    GPS_LONGITUDE = const(7)
    GPS_ELLIPSOID_ALT = const(8)
    GPS_MEAN_SEA_LVL_ALT = const(9)
    GPS_GDOP = const(10)
    GPS_PDOP = const(11)
    GPS_HDOP = const(12)
    GPS_VDOP = const(13)
    GPS_TDOP = const(14)
    GPS_ECEF_X = const(15)
    GPS_ECEF_Y = const(16)
    GPS_ECEF_Z = const(17)
    GPS_ECEF_VX = const(18)
    GPS_ECEF_VY = const(19)
    GPS_ECEF_VZ = const(20)


class PAYLOAD_IDX:
    pass


class STORAGE_IDX:
    NUM_FILES = const(0)
    DIR_SIZE = const(1)


"""
Helper function to get the number of attributes in a class
This result should be static
"""


def class_length(cls):
    return len([attr for attr in dir(cls) if not callable(getattr(cls, attr)) and not attr.startswith("__")])
