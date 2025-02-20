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

from apps.telemetry.constants import ADCS_IDX, CDH_IDX, EPS_IDX, GPS_IDX, STORAGE_IDX
from apps.telemetry.helpers import (
    convert_float_to_fixed_point_hp,
    pack_signed_long_int,
    pack_signed_short_int,
    pack_unsigned_long_int,
    pack_unsigned_short_int,
    unpack_unsigned_short_int,
)
from core import DataHandler as DH
from core import logger
from micropython import const


# No instantiation, the class acts as a namespace for the shared state
# Avoid global scope pollution and maintain consistency with the rest of the codebase
class TelemetryPacker:
    """
    Packs telemetry data for transmission
    """

    _TM_AVAILABLE = False

    _TM_FRAME_SIZE = const(248)  # size of the telemetry frame

    _FRAME = bytearray(_TM_FRAME_SIZE)  # pre-allocated buffer for packing
    _FRAME[0] = const(0x01) & 0xFF  # message ID
    _FRAME[1:3] = pack_unsigned_short_int([const(0x00)], 0)  # sequence count
    _FRAME[3] = const(229) & 0xFF  # packet length

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
    def pack_tm_heartbeat(cls):
        if not cls._TM_AVAILABLE:
            cls._TM_AVAILABLE = True

        cls._FRAME = bytearray(229 + 4)  # pre-allocated buffer for packing
        cls._FRAME[0] = const(0x01) & 0xFF  # message ID
        cls._FRAME[1:3] = pack_unsigned_short_int([const(0x00)], 0)  # sequence count
        cls._FRAME[3] = const(229) & 0xFF  # packet length

        ############ CDH fields ############
        if DH.data_process_exists("cdh"):
            cdh_data = DH.get_latest_data("cdh")

            if cdh_data:
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
                # Detumbling Error Flag
                cls._FRAME[17] = cdh_data[CDH_IDX.DETUMBLING_ERROR_FLAG] & 0xFF

            else:
                logger.warning("No latest CDH data available")

        else:
            logger.warning("No CDH data available")

        ############ EPS fields ############

        if DH.data_process_exists("eps"):
            eps_data = DH.get_latest_data("eps")

            if eps_data:
                # Low power flag
                cls._FRAME[18] = eps_data[EPS_IDX.EPS_POWER_FLAG] & 0xFF
                # CPU temperature
                cls._FRAME[19:21] = pack_signed_short_int(eps_data, EPS_IDX.CPU_TEMPERATURE)
                # Mainboard voltage
                cls._FRAME[21:23] = pack_signed_short_int(eps_data, EPS_IDX.MAINBOARD_VOLTAGE)
                # Mainboard current
                cls._FRAME[23:25] = pack_signed_short_int(eps_data, EPS_IDX.MAINBOARD_CURRENT)
                # Battery pack temperature
                cls._FRAME[25:27] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_PACK_TEMPERATURE)
                # Battery pack SOC
                cls._FRAME[27] = eps_data[EPS_IDX.BATTERY_PACK_REPORTED_SOC] & 0xFF
                # Battery pack capacity
                cls._FRAME[28:30] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_PACK_REPORTED_CAPACITY)
                # Battery pack current
                cls._FRAME[30:32] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_PACK_CURRENT)
                # Battery pack voltage
                cls._FRAME[32:34] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_PACK_VOLTAGE)
                # Battery pack midpoint voltage
                cls._FRAME[34:36] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_PACK_MIDPOINT_VOLTAGE)
                # Battery pack TTE
                cls._FRAME[36:40] = pack_unsigned_long_int(eps_data, EPS_IDX.BATTERY_PACK_TTE)
                # Battery pack TTF
                cls._FRAME[40:44] = pack_unsigned_long_int(eps_data, EPS_IDX.BATTERY_PACK_TTF)

                # XP coil voltage
                cls._FRAME[44:46] = pack_signed_short_int(eps_data, EPS_IDX.XP_COIL_VOLTAGE)
                # XP coil current
                cls._FRAME[46:48] = pack_signed_short_int(eps_data, EPS_IDX.XP_COIL_CURRENT)
                # XM coil voltage
                cls._FRAME[48:50] = pack_signed_short_int(eps_data, EPS_IDX.XM_COIL_VOLTAGE)
                # XM coil current
                cls._FRAME[50:52] = pack_signed_short_int(eps_data, EPS_IDX.XM_COIL_CURRENT)
                # YP coil voltage
                cls._FRAME[52:54] = pack_signed_short_int(eps_data, EPS_IDX.YP_COIL_VOLTAGE)
                # YP coil current
                cls._FRAME[54:56] = pack_signed_short_int(eps_data, EPS_IDX.YP_COIL_CURRENT)
                # YM coil voltage
                cls._FRAME[56:58] = pack_signed_short_int(eps_data, EPS_IDX.YM_COIL_VOLTAGE)
                # YM coil current
                cls._FRAME[58:60] = pack_signed_short_int(eps_data, EPS_IDX.YM_COIL_CURRENT)
                # ZP coil voltage
                cls._FRAME[60:62] = pack_signed_short_int(eps_data, EPS_IDX.ZP_COIL_VOLTAGE)
                # ZP coil current
                cls._FRAME[62:64] = pack_signed_short_int(eps_data, EPS_IDX.ZP_COIL_CURRENT)
                # ZM coil voltage
                cls._FRAME[64:66] = pack_signed_short_int(eps_data, EPS_IDX.ZM_COIL_VOLTAGE)
                # ZM coil current
                cls._FRAME[66:68] = pack_signed_short_int(eps_data, EPS_IDX.ZM_COIL_CURRENT)

                # Jetson input voltage
                cls._FRAME[68:70] = pack_signed_short_int(eps_data, EPS_IDX.JETSON_INPUT_VOLTAGE)
                # Jetson input current
                cls._FRAME[70:72] = pack_signed_short_int(eps_data, EPS_IDX.JETSON_INPUT_CURRENT)

                # RF LDO output voltage
                cls._FRAME[72:74] = pack_signed_short_int(eps_data, EPS_IDX.RF_LDO_OUTPUT_VOLTAGE)
                # RF LDO output current
                cls._FRAME[74:76] = pack_signed_short_int(eps_data, EPS_IDX.RF_LDO_OUTPUT_CURRENT)

                # GPS voltage
                cls._FRAME[76:78] = pack_signed_short_int(eps_data, EPS_IDX.GPS_VOLTAGE)
                # GPS current
                cls._FRAME[78:80] = pack_signed_short_int(eps_data, EPS_IDX.GPS_CURRENT)

                # XP solar charge voltage
                cls._FRAME[80:82] = pack_signed_short_int(eps_data, EPS_IDX.XP_SOLAR_CHARGE_VOLTAGE)
                # XP solar charge current
                cls._FRAME[82:84] = pack_signed_short_int(eps_data, EPS_IDX.XP_SOLAR_CHARGE_CURRENT)
                # XM solar charge voltage
                cls._FRAME[84:86] = pack_signed_short_int(eps_data, EPS_IDX.XM_SOLAR_CHARGE_VOLTAGE)
                # XM solar charge current
                cls._FRAME[86:88] = pack_signed_short_int(eps_data, EPS_IDX.XM_SOLAR_CHARGE_CURRENT)
                # YP solar charge voltage
                cls._FRAME[88:90] = pack_signed_short_int(eps_data, EPS_IDX.YP_SOLAR_CHARGE_VOLTAGE)
                # YP solar charge current
                cls._FRAME[90:92] = pack_signed_short_int(eps_data, EPS_IDX.YP_SOLAR_CHARGE_CURRENT)
                # YM solar charge voltage
                cls._FRAME[92:94] = pack_signed_short_int(eps_data, EPS_IDX.YM_SOLAR_CHARGE_VOLTAGE)
                # YM solar charge current
                cls._FRAME[94:96] = pack_signed_short_int(eps_data, EPS_IDX.YM_SOLAR_CHARGE_CURRENT)
                # ZP solar charge voltage
                cls._FRAME[96:98] = pack_signed_short_int(eps_data, EPS_IDX.ZP_SOLAR_CHARGE_VOLTAGE)
                # ZP solar charge current
                cls._FRAME[98:100] = pack_signed_short_int(eps_data, EPS_IDX.ZP_SOLAR_CHARGE_CURRENT)
                # ZM solar charge voltage
                cls._FRAME[100:102] = pack_signed_short_int(eps_data, EPS_IDX.ZM_SOLAR_CHARGE_VOLTAGE)
                # ZM solar charge current
                cls._FRAME[102:104] = pack_signed_short_int(eps_data, EPS_IDX.ZM_SOLAR_CHARGE_CURRENT)

            else:
                logger.warning("No latest EPS data available")
        else:
            logger.warning("No EPS data available")

        ############ ADCS fields ############
        if DH.data_process_exists("adcs"):
            adcs_data = DH.get_latest_data("adcs")

            if adcs_data:
                # ADCS state
                cls._FRAME[104] = adcs_data[ADCS_IDX.MODE] & 0xFF

                # Gyro X
                cls._FRAME[105:109] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.GYRO_X])
                # Gyro Y
                cls._FRAME[109:113] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.GYRO_Y])
                # Gyro Z
                cls._FRAME[113:117] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.GYRO_Z])

                # Magnetometer X
                cls._FRAME[117:121] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.MAG_X])
                # Magnetometer Y
                cls._FRAME[121:125] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.MAG_Y])
                # Magnetometer Z
                cls._FRAME[125:129] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.MAG_Z])

                # Sun status
                cls._FRAME[129] = adcs_data[ADCS_IDX.SUN_STATUS] & 0xFF
                # Sun vector X
                cls._FRAME[130:134] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.SUN_VEC_X])
                # Sun vector Y
                cls._FRAME[134:138] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.SUN_VEC_Y])
                # Sun vector Z
                cls._FRAME[138:142] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.SUN_VEC_Z])
                # Light sensor X+
                cls._FRAME[142:144] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_XP)
                # Light sensor X-
                cls._FRAME[144:146] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_XM)
                # Light sensor Y+
                cls._FRAME[146:148] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_YP)
                # Light sensor Y-
                cls._FRAME[148:150] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_YM)
                # Light sensor Z+ 1
                cls._FRAME[150:152] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZP1)
                # Light sensor Z+ 2
                cls._FRAME[152:154] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZP2)
                # Light sensor Z+ 3
                cls._FRAME[154:156] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZP3)
                # Light sensor Z+ 4
                cls._FRAME[156:158] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZP4)
                # Light sensor Z-
                cls._FRAME[158:160] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZM)

                # XP coil status
                cls._FRAME[160] = adcs_data[ADCS_IDX.XP_COIL_STATUS] & 0xFF
                # XM coil status
                cls._FRAME[161] = adcs_data[ADCS_IDX.XM_COIL_STATUS] & 0xFF
                # YP coil status
                cls._FRAME[162] = adcs_data[ADCS_IDX.YP_COIL_STATUS] & 0xFF
                # YM coil status
                cls._FRAME[163] = adcs_data[ADCS_IDX.YM_COIL_STATUS] & 0xFF
                # ZP coil status
                cls._FRAME[164] = adcs_data[ADCS_IDX.ZP_COIL_STATUS] & 0xFF
                # ZM coil status
                cls._FRAME[165] = adcs_data[ADCS_IDX.ZM_COIL_STATUS] & 0xFF

                # Coarse attitude QW
                cls._FRAME[166:170] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.ATTITUDE_QW])
                # Coarse attitude QX
                cls._FRAME[170:174] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.ATTITUDE_QX])
                # Coarse attitude QY
                cls._FRAME[174:178] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.ATTITUDE_QY])
                # Coarse attitude QZ
                cls._FRAME[178:182] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.ATTITUDE_QZ])

            else:
                logger.warning("No latest ADCS data available")
        else:
            logger.warning("No ADCS data available")

        ############ GPS fields ############
        if DH.data_process_exists("gps"):
            gps_data = DH.get_latest_data("gps")

            if gps_data:
                # message ID
                cls._FRAME[182] = gps_data[GPS_IDX.GPS_MESSAGE_ID] & 0xFF
                # fix mode
                cls._FRAME[183] = gps_data[GPS_IDX.GPS_FIX_MODE] & 0xFF
                # number of SV
                cls._FRAME[184] = gps_data[GPS_IDX.GPS_NUMBER_OF_SV] & 0xFF
                # GNSS week
                cls._FRAME[185:187] = pack_unsigned_short_int(gps_data, GPS_IDX.GPS_GNSS_WEEK)
                # GNSS TOW
                cls._FRAME[187:191] = pack_unsigned_long_int(gps_data, GPS_IDX.GPS_GNSS_TOW)
                # latitude
                cls._FRAME[191:195] = pack_signed_long_int(gps_data, GPS_IDX.GPS_LATITUDE)
                # longitude
                cls._FRAME[195:199] = pack_signed_long_int(gps_data, GPS_IDX.GPS_LONGITUDE)
                # ellipsoid altitude
                cls._FRAME[199:203] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ELLIPSOID_ALT)
                # mean sea level altitude
                cls._FRAME[203:207] = pack_signed_long_int(gps_data, GPS_IDX.GPS_MEAN_SEA_LVL_ALT)
                # ECEF X
                cls._FRAME[207:211] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_X)
                # ECEF Y
                cls._FRAME[211:215] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_Y)
                # ECEF Z
                cls._FRAME[215:219] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_Z)
                # ECEF VX
                cls._FRAME[219:223] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_VX)
                # ECEF VY
                cls._FRAME[223:227] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_VY)
                # ECEF VZ
                cls._FRAME[227:231] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_VZ)
            else:
                logger.warning("No latest GPS data available")
        else:
            logger.warning("No GPS data available")

        cls._FRAME[:] = bytearray(cls._FRAME[:])
        gc.collect()

        ############ Payload status fields ############
        # TODO

        return True

    @classmethod
    def pack_tm_hal(cls):
        # TODO: HAL status, error codes, EPS
        if not cls._TM_AVAILABLE:
            cls._TM_AVAILABLE = True

        # TODO: Frame definition for TM_HAL
        cls._FRAME = bytearray(13 + 4)  # pre-allocated buffer for packing
        cls._FRAME[0] = const(0x02) & 0xFF  # message ID
        cls._FRAME[1:3] = pack_unsigned_short_int([const(0x00)], 0)  # sequence count
        cls._FRAME[3] = const(13) & 0xFF  # packet length

        ############ CDH fields ############
        if DH.data_process_exists("cdh"):
            cdh_data = DH.get_latest_data("cdh")

            if cdh_data:
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
                # Detumbling Error Flag
                cls._FRAME[17] = cdh_data[CDH_IDX.DETUMBLING_ERROR_FLAG] & 0xFF

            else:
                logger.warning("No latest CDH data available")

        else:
            logger.warning("No CDH data available")
        pass

    @classmethod
    def pack_tm_storage(cls):
        if not cls._TM_AVAILABLE:
            cls._TM_AVAILABLE = True

        cls._FRAME = bytearray(72 + 4)  # pre-allocated buffer for packing
        cls._FRAME[0] = const(0x03) & 0xFF  # message ID
        cls._FRAME[1:3] = pack_unsigned_short_int([const(0x00)], 0)  # sequence count
        cls._FRAME[3] = const(72) & 0xFF  # packet length

        ############ CDH fields ############
        if DH.data_process_exists("cdh"):
            cdh_data = DH.get_latest_data("cdh")

            if cdh_data:
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
                # Detumbling Error Flag
                cls._FRAME[17] = cdh_data[CDH_IDX.DETUMBLING_ERROR_FLAG] & 0xFF

            else:
                logger.warning("No latest CDH data available")

        else:
            logger.warning("No CDH data available")

        # Total SD card usage
        cls._FRAME[18:22] = pack_signed_long_int([DH.SD_usage()], 0)

        ############ CDH fields ###########
        if DH.data_process_exists("cdh"):
            cdh_storage_info = DH.get_storage_info("cdh")
            # CDH number of files
            cls._FRAME[22:26] = pack_signed_long_int(cdh_storage_info, STORAGE_IDX.NUM_FILES)
            # CDH directory size
            cls._FRAME[26:30] = pack_signed_long_int(cdh_storage_info, STORAGE_IDX.DIR_SIZE)
        else:
            logger.warning("CDH Data process does not exist")

        ############ EPS fields ###########
        if DH.data_process_exists("eps"):
            eps_storage_info = DH.get_storage_info("eps")
            # EPS number of files
            cls._FRAME[30:34] = pack_signed_long_int(eps_storage_info, STORAGE_IDX.NUM_FILES)
            # EPS directory size
            cls._FRAME[34:38] = pack_signed_long_int(eps_storage_info, STORAGE_IDX.DIR_SIZE)
        else:
            logger.warning("EPS Data process does not exist")

        ############ ADCS fields ###########
        if DH.data_process_exists("adcs"):
            adcs_storage_info = DH.get_storage_info("adcs")
            # ADCS number of files
            cls._FRAME[38:42] = pack_signed_long_int(adcs_storage_info, STORAGE_IDX.NUM_FILES)
            # ADCS directory size
            cls._FRAME[42:46] = pack_signed_long_int(adcs_storage_info, STORAGE_IDX.DIR_SIZE)
        else:
            logger.warning("ADCS Data process does not exist")

        ############ COMMS fields ###########
        if DH.data_process_exists("comms"):
            comms_storage_info = DH.get_storage_info("comms")
            # COMMS number of files
            cls._FRAME[46:50] = pack_signed_long_int(comms_storage_info, STORAGE_IDX.NUM_FILES)
            # COMMS directory size
            cls._FRAME[50:54] = pack_signed_long_int(comms_storage_info, STORAGE_IDX.DIR_SIZE)
        else:
            logger.warning("Comms Data process does not exist")

        ############ GPS fields ###########
        if DH.data_process_exists("gps"):
            gps_storage_info = DH.get_storage_info("gps")
            # GPS number of files
            cls._FRAME[54:58] = pack_signed_long_int(gps_storage_info, STORAGE_IDX.NUM_FILES)
            # GPS directory size
            cls._FRAME[58:62] = pack_signed_long_int(gps_storage_info, STORAGE_IDX.DIR_SIZE)
        else:
            logger.warning("GPS Data process does not exist")

        ############ Payload fields ###########
        if DH.data_process_exists("payload"):
            payload_storage_info = DH.get_storage_info("payload")
            # PAYLOAD number of files
            cls._FRAME[62:66] = pack_signed_long_int(payload_storage_info, STORAGE_IDX.NUM_FILES)
            # PAYLOAD directory size
            cls._FRAME[66:70] = pack_signed_long_int(payload_storage_info, STORAGE_IDX.DIR_SIZE)
        else:
            logger.warning("Payload Data process does not exist")

        ############ Thermal fields ###########
        if DH.data_process_exists("thermal"):
            thermal_storage_info = DH.get_storage_info("thermal")
            # THERMAL number of files
            cls._FRAME[70:74] = pack_signed_long_int(thermal_storage_info, STORAGE_IDX.NUM_FILES)
            # THERMAL directory size
            cls._FRAME[74:78] = pack_signed_long_int(thermal_storage_info, STORAGE_IDX.DIR_SIZE)
        else:
            logger.warning("Thermal Data process does not exist")

        ############ Command fields ###########
        if DH.data_process_exists("cmd_logs"):
            cmd_logs_storage_info = DH.get_storage_info("cmd_logs")
            # Command logs number of files
            cls._FRAME[78:82] = pack_signed_long_int(cmd_logs_storage_info, STORAGE_IDX.NUM_FILES)
            # Command logs directory size
            cls._FRAME[82:86] = pack_signed_long_int(cmd_logs_storage_info, STORAGE_IDX.DIR_SIZE)
        else:
            logger.warning("Command logs Data process does not exist")

        # ############ Image fields ###########
        # if DH.data_process_exists("img"):
        #     img_logs_storage_info = DH.get_storage_info("img")
        #     # Image number of files
        #     cls._FRAME[86:90] = pack_signed_long_int(img_logs_storage_info, STORAGE_IDX.NUM_FILES)
        #     # Image directory size
        #     cls._FRAME[90:94] = pack_signed_long_int(img_logs_storage_info, STORAGE_IDX.DIR_SIZE)
        # else:
        #     logger.warning("IMG Data process does not exist")

    @classmethod
    def pack_tm_payload(cls):
        pass
