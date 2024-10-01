"""

Telemetry packing for transmission

Each fixed-length LoRa Payload is structured as follows
MESSAGE_ID : 1 byte
SEQ_COUNT  : 2 byte
PACKET_LENGTH: 1 byte
PACKET_DATA  : 252 bytes (for now)

For struct module format strings:
    "b": 1,  # byte
    "B": 1,  # unsigned byte
    "h": 2,  # short
    "H": 2,  # unsigned short
    "i": 4,  # int
    "I": 4,  # unsigned int
    "l": 4,  # long
    "L": 4,  # unsigned long
    "q": 8,  # long long
    "Q": 8,  # unsigned long long
    "f": 4,  # float
    "d": 8,  # double

"""
import gc

from apps.telemetry.constants import ADCS_IDX, CDH_IDX, EPS_IDX, GPS_IDX, THERMAL_IDX
from apps.telemetry.helpers import (
    convert_float_to_fixed_point_hp,
    pack_signed_long_int,
    pack_signed_short_int,
    pack_unsigned_long_int,
    pack_unsigned_short_int,
    unpack_unsigned_short_int,
)
from core import logger
from core.data_handler import DataHandler as DH
from micropython import const


# No instantiation, the class acts as a namespace for the shared state
# Avoid global scope pollution and maintain consistency with the rest of the codebase
class TelemetryPacker:
    """
    Packs telemetry data for transmission
    """

    _TM_AVAILABLE = False

    _TM_FRAME_SIZE = const(250)  # size of the telemetry frame

    _FRAME = bytearray(_TM_FRAME_SIZE)  # pre-allocated buffer for packing
    _FRAME[0] = const(0x01) & 0xFF  # message ID
    _FRAME[1:3] = pack_unsigned_short_int([const(0x00)], 0)  # sequence count
    _FRAME[3] = const(245) & 0xFF  # packet length

    @classmethod
    def FRAME(cls):
        return cls._FRAME

    @classmethod
    def FRAME_SIZE(cls):
        return cls._TM_FRAME_SIZE

    @classmethod
    def SEQ_COUNT(cls):
        return unpack_unsigned_short_int(cls._FRAME[1:3])

    @classmethod
    def PACKET_LENGTH(cls):
        return cls._FRAME[3]

    @classmethod
    def TM_AVAILABLE(cls):
        return cls._TM_AVAILABLE

    @classmethod
    def pack_tm_frame(cls):

        if not cls._TM_AVAILABLE:
            cls._TM_AVAILABLE = True

        ############ CDH fields ############
        if DH.data_process_exists("cdh"):

            cdh_data = DH.get_latest_data("cdh")

            # Time
            cls._FRAME[4:8] = pack_unsigned_long_int(cdh_data, CDH_IDX.TIME)

            # SC State
            cls._FRAME[8] = cdh_data[CDH_IDX.SC_STATE] & 0xFF
            # SD Usage
            cls._FRAME[9:13] = pack_unsigned_long_int(cdh_data, CDH_IDX.SD_USAGE)
            # Current RAM Usage
            cls._FRAME[13] = cdh_data[CDH_IDX.CURRENT_RAM_USAGE] & 0xFF
            # Reboot count
            cls._FRAME[14] = cdh_data[CDH_IDX.REBOOT_COUNT] & 0xFF
            # Watchdog Timer
            cls._FRAME[15] = cdh_data[CDH_IDX.WATCHDOG_TIMER] & 0xFF
            # HAL Bitflags
            cls._FRAME[16] = cdh_data[CDH_IDX.HAL_BITFLAGS] & 0xFF

        else:
            logger.error("No CDH data available")

        ############ EPS fields ############

        if DH.data_process_exists("eps"):
            eps_data = DH.get_latest_data("eps")

            # Mainboard voltage
            cls._FRAME[17:19] = pack_signed_short_int(eps_data, EPS_IDX.MAINBOARD_VOLTAGE)
            # Mainboard current
            cls._FRAME[19:21] = pack_signed_short_int(eps_data, EPS_IDX.MAINBOARD_CURRENT)
            # Battery pack SOC
            cls._FRAME[21] = eps_data[EPS_IDX.BATTERY_PACK_REPORTED_SOC] & 0xFF
            # Battery pack capacity
            cls._FRAME[22:24] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_PACK_REPORTED_CAPACITY)
            # Battery pack current
            cls._FRAME[24:26] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_PACK_CURRENT)
            # Battery pack voltage
            cls._FRAME[26:28] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_PACK_VOLTAGE)
            # Battery pack midpoint voltage
            cls._FRAME[28:30] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_PACK_MIDPOINT_VOLTAGE)
            # Battery cycles
            cls._FRAME[30:32] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_CYCLES)
            # Battery pack TTE
            cls._FRAME[32:34] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_PACK_TTE)
            # Battery pack TTF
            cls._FRAME[34:36] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_PACK_TTF)
            # Battery time since power up
            cls._FRAME[36:38] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_TIME_SINCE_POWER_UP)

            # XP coil voltage
            cls._FRAME[38:40] = pack_signed_short_int(eps_data, EPS_IDX.XP_COIL_VOLTAGE)
            # XP coil current
            cls._FRAME[40:42] = pack_signed_short_int(eps_data, EPS_IDX.XP_COIL_CURRENT)
            # XM coil voltage
            cls._FRAME[42:44] = pack_signed_short_int(eps_data, EPS_IDX.XM_COIL_VOLTAGE)
            # XM coil current
            cls._FRAME[44:46] = pack_signed_short_int(eps_data, EPS_IDX.XM_COIL_CURRENT)
            # YP coil voltage
            cls._FRAME[46:48] = pack_signed_short_int(eps_data, EPS_IDX.YP_COIL_VOLTAGE)
            # YP coil current
            cls._FRAME[48:50] = pack_signed_short_int(eps_data, EPS_IDX.YP_COIL_CURRENT)
            # YM coil voltage
            cls._FRAME[50:52] = pack_signed_short_int(eps_data, EPS_IDX.YM_COIL_VOLTAGE)
            # YM coil current
            cls._FRAME[52:54] = pack_signed_short_int(eps_data, EPS_IDX.YM_COIL_CURRENT)
            # ZP coil voltage
            cls._FRAME[54:56] = pack_signed_short_int(eps_data, EPS_IDX.ZP_COIL_VOLTAGE)
            # ZP coil current
            cls._FRAME[56:58] = pack_signed_short_int(eps_data, EPS_IDX.ZP_COIL_CURRENT)
            # ZM coil voltage
            cls._FRAME[58:60] = pack_signed_short_int(eps_data, EPS_IDX.ZM_COIL_VOLTAGE)
            # ZM coil current
            cls._FRAME[60:62] = pack_signed_short_int(eps_data, EPS_IDX.ZM_COIL_CURRENT)

            # Jetson input voltage
            cls._FRAME[62:64] = pack_signed_short_int(eps_data, EPS_IDX.JETSON_INPUT_VOLTAGE)
            # Jetson input current
            cls._FRAME[64:66] = pack_signed_short_int(eps_data, EPS_IDX.JETSON_INPUT_CURRENT)

            # RF LDO output voltage
            cls._FRAME[66:68] = pack_signed_short_int(eps_data, EPS_IDX.RF_LDO_OUTPUT_VOLTAGE)
            # RF LDO output current
            cls._FRAME[68:70] = pack_signed_short_int(eps_data, EPS_IDX.RF_LDO_OUTPUT_CURRENT)

            # GPS voltage
            cls._FRAME[70:72] = pack_signed_short_int(eps_data, EPS_IDX.GPS_VOLTAGE)
            # GPS current
            cls._FRAME[72:74] = pack_signed_short_int(eps_data, EPS_IDX.GPS_CURRENT)

            # XP solar charge voltage
            cls._FRAME[74:76] = pack_signed_short_int(eps_data, EPS_IDX.XP_SOLAR_CHARGE_VOLTAGE)
            # XP solar charge current
            cls._FRAME[76:78] = pack_signed_short_int(eps_data, EPS_IDX.XP_SOLAR_CHARGE_CURRENT)
            # XM solar charge voltage
            cls._FRAME[78:80] = pack_signed_short_int(eps_data, EPS_IDX.XM_SOLAR_CHARGE_VOLTAGE)
            # XM solar charge current
            cls._FRAME[80:82] = pack_signed_short_int(eps_data, EPS_IDX.XM_SOLAR_CHARGE_CURRENT)
            # YP solar charge voltage
            cls._FRAME[82:84] = pack_signed_short_int(eps_data, EPS_IDX.YP_SOLAR_CHARGE_VOLTAGE)
            # YP solar charge current
            cls._FRAME[84:86] = pack_signed_short_int(eps_data, EPS_IDX.YP_SOLAR_CHARGE_CURRENT)
            # YM solar charge voltage
            cls._FRAME[86:88] = pack_signed_short_int(eps_data, EPS_IDX.YM_SOLAR_CHARGE_VOLTAGE)
            # YM solar charge current
            cls._FRAME[88:90] = pack_signed_short_int(eps_data, EPS_IDX.YM_SOLAR_CHARGE_CURRENT)
            # ZP solar charge voltage
            cls._FRAME[90:92] = pack_signed_short_int(eps_data, EPS_IDX.ZP_SOLAR_CHARGE_VOLTAGE)
            # ZP solar charge current
            cls._FRAME[92:94] = pack_signed_short_int(eps_data, EPS_IDX.ZP_SOLAR_CHARGE_CURRENT)
            # ZM solar charge voltage
            cls._FRAME[94:96] = pack_signed_short_int(eps_data, EPS_IDX.ZM_SOLAR_CHARGE_VOLTAGE)
            # ZM solar charge current
            cls._FRAME[96:98] = pack_signed_short_int(eps_data, EPS_IDX.ZM_SOLAR_CHARGE_CURRENT)
        else:
            logger.error("No EPS data available")

        ############ ADCS fields ############
        if DH.data_process_exists("adcs"):

            adcs_data = DH.get_latest_data("adcs")

            # ADCS state
            cls._FRAME[98] = adcs_data[ADCS_IDX.ADCS_STATE] & 0xFF

            # Gyro X
            cls._FRAME[99:103] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.GYRO_X])
            # Gyro Y
            cls._FRAME[103:107] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.GYRO_Y])
            # Gyro Z
            cls._FRAME[107:111] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.GYRO_Z])

            # Magnetometer X
            cls._FRAME[111:115] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.MAG_X])
            # Magnetometer Y
            cls._FRAME[115:119] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.MAG_Y])
            # Magnetometer Z
            cls._FRAME[119:123] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.MAG_Z])

            # Sun status
            cls._FRAME[123] = adcs_data[ADCS_IDX.SUN_STATUS] & 0xFF
            # Sun vector X
            cls._FRAME[124:128] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.SUN_VEC_X])
            # Sun vector Y
            cls._FRAME[128:132] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.SUN_VEC_Y])
            # Sun vector Z
            cls._FRAME[132:136] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.SUN_VEC_Z])
            # Eclipse bool
            cls._FRAME[136] = adcs_data[ADCS_IDX.ECLIPSE] & 0xFF
            # Light sensor X+
            cls._FRAME[137:139] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_XP)
            # Light sensor X-
            cls._FRAME[139:141] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_XM)
            # Light sensor Y+
            cls._FRAME[141:143] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_YP)
            # Light sensor Y-
            cls._FRAME[143:145] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_YM)
            # Light sensor Z+ 1
            cls._FRAME[145:147] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZP1)
            # Light sensor Z+ 2
            cls._FRAME[147:149] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZP2)
            # Light sensor Z+ 3
            cls._FRAME[149:151] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZP3)
            # Light sensor Z+ 4
            cls._FRAME[151:153] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZP4)
            # Light sensor Z-
            cls._FRAME[153:155] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZM)

            # XP coil status
            cls._FRAME[155] = adcs_data[ADCS_IDX.XP_COIL_STATUS] & 0xFF
            # XM coil status
            cls._FRAME[156] = adcs_data[ADCS_IDX.XM_COIL_STATUS] & 0xFF
            # YP coil status
            cls._FRAME[157] = adcs_data[ADCS_IDX.YP_COIL_STATUS] & 0xFF
            # YM coil status
            cls._FRAME[158] = adcs_data[ADCS_IDX.YM_COIL_STATUS] & 0xFF
            # ZP coil status
            cls._FRAME[159] = adcs_data[ADCS_IDX.ZP_COIL_STATUS] & 0xFF
            # ZM coil status
            cls._FRAME[160] = adcs_data[ADCS_IDX.ZM_COIL_STATUS] & 0xFF

            # Coarse attitude QW
            cls._FRAME[161:165] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.COARSE_ATTITUDE_QW])
            # Coarse attitude QX
            cls._FRAME[165:169] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.COARSE_ATTITUDE_QX])
            # Coarse attitude QY
            cls._FRAME[169:173] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.COARSE_ATTITUDE_QY])
            # Coarse attitude QZ
            cls._FRAME[173:177] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.COARSE_ATTITUDE_QZ])

            # Star tracker status
            cls._FRAME[177] = adcs_data[ADCS_IDX.STAR_TRACKER_STATUS] & 0xFF

            # Star tracker attitude QW
            cls._FRAME[178:182] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.STAR_TRACKER_ATTITUDE_QW])
            # Star tracker attitude QX
            cls._FRAME[182:186] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.STAR_TRACKER_ATTITUDE_QX])
            # Star tracker attitude QY
            cls._FRAME[186:190] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.STAR_TRACKER_ATTITUDE_QY])
            # Star tracker attitude QZ
            cls._FRAME[190:194] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.STAR_TRACKER_ATTITUDE_QZ])
        else:
            logger.error("No ADCS data available")

        ############ GPS fields ############
        if DH.data_process_exists("gps"):

            gps_data = DH.get_latest_data("gps")

            # message ID
            cls._FRAME[194] = gps_data[GPS_IDX.GPS_MESSAGE_ID] & 0xFF
            # fix mode
            cls._FRAME[195] = gps_data[GPS_IDX.GPS_FIX_MODE] & 0xFF
            # number of SV
            cls._FRAME[196] = gps_data[GPS_IDX.GPS_NUMBER_OF_SV] & 0xFF
            # GNSS week
            cls._FRAME[197:199] = pack_unsigned_short_int(gps_data, GPS_IDX.GPS_GNSS_WEEK)
            # GNSS TOW
            cls._FRAME[199:203] = pack_unsigned_long_int(gps_data, GPS_IDX.GPS_GNSS_TOW)
            # latitude
            cls._FRAME[203:207] = pack_signed_long_int(gps_data, GPS_IDX.GPS_LATITUDE)
            # longitude
            cls._FRAME[207:211] = pack_signed_long_int(gps_data, GPS_IDX.GPS_LONGITUDE)
            # ellipsoid altitude
            cls._FRAME[211:215] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ELLIPSOID_ALT)
            # mean sea level altitude
            cls._FRAME[215:219] = pack_signed_long_int(gps_data, GPS_IDX.GPS_MEAN_SEA_LVL_ALT)

            # ECEF X
            cls._FRAME[219:223] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_X)
            # ECEF Y
            cls._FRAME[223:227] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_Y)
            # ECEF Z
            cls._FRAME[227:231] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_Z)
            # ECEF VX
            cls._FRAME[231:235] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_VX)
            # ECEF VY
            cls._FRAME[235:239] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_VY)
            # ECEF VZ
            cls._FRAME[239:243] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_VZ)
        else:
            logger.error("No GPS data available")

        ############ Thermal fields ############

        if DH.data_process_exists("thermal"):
            thermal_data = DH.get_latest_data("thermal")

            # IMU temperature
            cls._FRAME[243:245] = pack_unsigned_short_int(thermal_data, THERMAL_IDX.IMU_TEMPERATURE)
            # CPU temperature
            cls._FRAME[245:247] = pack_unsigned_short_int(thermal_data, THERMAL_IDX.CPU_TEMPERATURE)
            # Battery temperature
            cls._FRAME[247:249] = pack_unsigned_short_int(thermal_data, THERMAL_IDX.BATTERY_PACK_TEMPERATURE)

        else:
            logger.error("No Thermal data available")

        cls._FRAME[:] = bytearray(cls._FRAME[:])
        gc.collect()

        ############ Payload fields ############
        # TODO

        return True
