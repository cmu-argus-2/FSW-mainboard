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

from apps.telemetry.constants import ADCS_IDX, CDH_IDX, EPS_IDX, EPS_WARNING_IDX, GPS_IDX, STORAGE_IDX
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

# TM frame sizes as defined in message database
# TODO: TM HAL
# TODO: TM PAYLOAD
_TM_NOMINAL_SIZE = const(230)
_TM_HAL_SIZE = const(46)
_TM_STORAGE_SIZE = const(74)
_TM_PAYLOAD_SIZE = const(0)


# No instantiation, the class acts as a namespace for the shared state
# Avoid global scope pollution and maintain consistency with the rest of the codebase
class TelemetryPacker:
    """
    Packs telemetry data for transmission
    """

    _TM_AVAILABLE = False

    # Maximum allowed size of the telemetry frame
    _TM_FRAME_SIZE = const(248)

    # Frame size and packet length SHALL be updated for every TM frame definition
    _FRAME = bytearray(_TM_FRAME_SIZE)  # pre-allocated buffer for packing
    _FRAME[0] = const(0x01) & 0xFF  # message ID
    _FRAME[1:3] = pack_unsigned_short_int([const(0x00)], 0)  # sequence count
    _FRAME[3] = const(_TM_FRAME_SIZE) & 0xFF  # packet length

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

        cls._FRAME = bytearray(_TM_NOMINAL_SIZE + 4)  # pre-allocated buffer for packing
        cls._FRAME[0] = const(0x01) & 0xFF  # message ID
        cls._FRAME[1:3] = pack_unsigned_short_int([const(0x00)], 0)  # sequence count
        cls._FRAME[3] = const(_TM_NOMINAL_SIZE) & 0xFF  # packet length

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
                cls._FRAME[19:21] = pack_signed_short_int(eps_data, EPS_IDX.MAINBOARD_TEMPERATURE)
                # Mainboard voltage
                cls._FRAME[21:23] = pack_signed_short_int(eps_data, EPS_IDX.MAINBOARD_VOLTAGE)
                # Mainboard current
                cls._FRAME[23:25] = pack_signed_short_int(eps_data, EPS_IDX.MAINBOARD_CURRENT)
                # Battery pack temperature
                cls._FRAME[25:27] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_PACK_TEMPERATURE)
                # Battery pack SOC
                cls._FRAME[27] = eps_data[EPS_IDX.BATTERY_PACK_REPORTED_SOC] & 0xFF
                # Battery pack capacity
                cls._FRAME[28:30] = pack_unsigned_short_int(eps_data, EPS_IDX.BATTERY_PACK_REPORTED_CAPACITY)
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

        ############ EPS warning fields ############
        if DH.data_process_exists("eps_warning"):
            eps_warning_data = DH.get_latest_data("eps_warning")

            if eps_warning_data:
                cls._FRAME[104] = eps_warning_data[EPS_WARNING_IDX.MAINBOARD_POWER_ALERT] & 0xFF
                cls._FRAME[105] = eps_warning_data[EPS_WARNING_IDX.RADIO_POWER_ALERT] & 0xFF
                cls._FRAME[106] = eps_warning_data[EPS_WARNING_IDX.JETSON_POWER_ALERT] & 0xFF

        ############ ADCS fields ############
        if DH.data_process_exists("adcs"):
            adcs_data = DH.get_latest_data("adcs")

            if adcs_data:
                # ADCS state
                cls._FRAME[107] = adcs_data[ADCS_IDX.MODE] & 0xFF

                # Gyro X
                cls._FRAME[108:112] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.GYRO_X])
                # Gyro Y
                cls._FRAME[112:116] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.GYRO_Y])
                # Gyro Z
                cls._FRAME[116:120] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.GYRO_Z])

                # Magnetometer X
                cls._FRAME[120:124] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.MAG_X])
                # Magnetometer Y
                cls._FRAME[124:128] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.MAG_Y])
                # Magnetometer Z
                cls._FRAME[128:132] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.MAG_Z])

                # Sun status
                cls._FRAME[132] = adcs_data[ADCS_IDX.SUN_STATUS] & 0xFF
                # Sun vector X
                cls._FRAME[133:137] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.SUN_VEC_X])
                # Sun vector Y
                cls._FRAME[137:141] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.SUN_VEC_Y])
                # Sun vector Z
                cls._FRAME[141:145] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.SUN_VEC_Z])
                # Light sensor X+
                cls._FRAME[145:147] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_XP)
                # Light sensor X-
                cls._FRAME[147:149] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_XM)
                # Light sensor Y+
                cls._FRAME[149:151] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_YP)
                # Light sensor Y-
                cls._FRAME[151:153] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_YM)
                # Light sensor Z+ 1
                cls._FRAME[153:155] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZP1)
                # Light sensor Z+ 2
                cls._FRAME[155:157] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZP2)
                # Light sensor Z+ 3
                cls._FRAME[157:159] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZP3)
                # Light sensor Z+ 4
                cls._FRAME[159:161] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZP4)
                # Light sensor Z-
                cls._FRAME[161:163] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZM)

                # XP coil status
                cls._FRAME[163] = adcs_data[ADCS_IDX.XP_COIL_STATUS] & 0xFF
                # XM coil status
                cls._FRAME[164] = adcs_data[ADCS_IDX.XM_COIL_STATUS] & 0xFF
                # YP coil status
                cls._FRAME[165] = adcs_data[ADCS_IDX.YP_COIL_STATUS] & 0xFF
                # YM coil status
                cls._FRAME[166] = adcs_data[ADCS_IDX.YM_COIL_STATUS] & 0xFF
                # ZP coil status
                cls._FRAME[167] = adcs_data[ADCS_IDX.ZP_COIL_STATUS] & 0xFF
                # ZM coil status
                cls._FRAME[168] = adcs_data[ADCS_IDX.ZM_COIL_STATUS] & 0xFF

                # Coarse attitude QW
                cls._FRAME[169:173] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.ATTITUDE_QW])
                # Coarse attitude QX
                cls._FRAME[173:177] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.ATTITUDE_QX])
                # Coarse attitude QY
                cls._FRAME[177:181] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.ATTITUDE_QY])
                # Coarse attitude QZ
                cls._FRAME[181:185] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.ATTITUDE_QZ])

            else:
                logger.warning("No latest ADCS data available")
        else:
            logger.warning("No ADCS data available")

        ############ GPS fields ############
        if DH.data_process_exists("gps"):
            gps_data = DH.get_latest_data("gps")

            if gps_data:
                # message ID
                cls._FRAME[185] = gps_data[GPS_IDX.GPS_MESSAGE_ID] & 0xFF
                # fix mode
                cls._FRAME[186] = gps_data[GPS_IDX.GPS_FIX_MODE] & 0xFF
                # number of SV
                cls._FRAME[187] = gps_data[GPS_IDX.GPS_NUMBER_OF_SV] & 0xFF
                # GNSS week
                cls._FRAME[188:190] = pack_unsigned_short_int(gps_data, GPS_IDX.GPS_GNSS_WEEK)
                # GNSS TOW
                cls._FRAME[190:194] = pack_unsigned_long_int(gps_data, GPS_IDX.GPS_GNSS_TOW)
                # latitude
                cls._FRAME[194:198] = pack_signed_long_int(gps_data, GPS_IDX.GPS_LATITUDE)
                # longitude
                cls._FRAME[198:202] = pack_signed_long_int(gps_data, GPS_IDX.GPS_LONGITUDE)
                # ellipsoid altitude
                cls._FRAME[202:206] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ELLIPSOID_ALT)
                # mean sea level altitude
                cls._FRAME[206:210] = pack_signed_long_int(gps_data, GPS_IDX.GPS_MEAN_SEA_LVL_ALT)
                # ECEF X
                cls._FRAME[210:214] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_X)
                # ECEF Y
                cls._FRAME[214:218] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_Y)
                # ECEF Z
                cls._FRAME[218:222] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_Z)
                # ECEF VX
                cls._FRAME[222:226] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_VX)
                # ECEF VY
                cls._FRAME[226:230] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_VY)
                # ECEF VZ
                cls._FRAME[230:234] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_VZ)
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
        cls._FRAME = bytearray(_TM_HAL_SIZE + 4)  # pre-allocated buffer for packing
        cls._FRAME[0] = const(0x02) & 0xFF  # message ID
        cls._FRAME[1:3] = pack_unsigned_short_int([const(0x00)], 0)  # sequence count
        cls._FRAME[3] = const(_TM_HAL_SIZE) & 0xFF  # packet length

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

        cls._FRAME = bytearray(_TM_STORAGE_SIZE + 4)  # pre-allocated buffer for packing
        cls._FRAME[0] = const(0x03) & 0xFF  # message ID
        cls._FRAME[1:3] = pack_unsigned_short_int([const(0x00)], 0)  # sequence count
        cls._FRAME[3] = const(_TM_STORAGE_SIZE) & 0xFF  # packet length

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
        cls._FRAME[18:22] = pack_unsigned_long_int([DH.SD_usage()], 0)

        ############ CDH fields ###########
        if DH.data_process_exists("cdh"):
            cdh_storage_info = DH.get_storage_info("cdh")
            # CDH number of files
            cls._FRAME[22:26] = pack_unsigned_long_int(cdh_storage_info, STORAGE_IDX.NUM_FILES)
            # CDH directory size
            cls._FRAME[26:30] = pack_unsigned_long_int(cdh_storage_info, STORAGE_IDX.DIR_SIZE)
        else:
            logger.warning("CDH Data process does not exist")

        ############ EPS fields ###########
        if DH.data_process_exists("eps"):
            eps_storage_info = DH.get_storage_info("eps")
            # EPS number of files
            cls._FRAME[30:34] = pack_unsigned_long_int(eps_storage_info, STORAGE_IDX.NUM_FILES)
            # EPS directory size
            cls._FRAME[34:38] = pack_unsigned_long_int(eps_storage_info, STORAGE_IDX.DIR_SIZE)
        else:
            logger.warning("EPS Data process does not exist")

        ############ EPS Warning fields ###########
        if DH.data_process_exists("eps_warning"):
            eps_warning_storage_info = DH.get_storage_info("eps_warning")
            # EPS number of files
            cls._FRAME[38:42] = pack_unsigned_long_int(eps_warning_storage_info, STORAGE_IDX.NUM_FILES)
            # EPS directory size
            cls._FRAME[42:46] = pack_unsigned_long_int(eps_warning_storage_info, STORAGE_IDX.DIR_SIZE)
        else:
            logger.warning("EPS Warning Data process does not exist")

        ############ ADCS fields ###########
        if DH.data_process_exists("adcs"):
            adcs_storage_info = DH.get_storage_info("adcs")
            # ADCS number of files
            cls._FRAME[38:42] = pack_unsigned_long_int(adcs_storage_info, STORAGE_IDX.NUM_FILES)
            # ADCS directory size
            cls._FRAME[42:46] = pack_unsigned_long_int(adcs_storage_info, STORAGE_IDX.DIR_SIZE)
        else:
            logger.warning("ADCS Data process does not exist")

        ############ COMMS fields ###########
        if DH.data_process_exists("comms"):
            comms_storage_info = DH.get_storage_info("comms")
            # COMMS number of files
            cls._FRAME[46:50] = pack_unsigned_long_int(comms_storage_info, STORAGE_IDX.NUM_FILES)
            # COMMS directory size
            cls._FRAME[50:54] = pack_unsigned_long_int(comms_storage_info, STORAGE_IDX.DIR_SIZE)
        else:
            logger.warning("Comms Data process does not exist")

        ############ GPS fields ###########
        if DH.data_process_exists("gps"):
            gps_storage_info = DH.get_storage_info("gps")
            # GPS number of files
            cls._FRAME[54:58] = pack_unsigned_long_int(gps_storage_info, STORAGE_IDX.NUM_FILES)
            # GPS directory size
            cls._FRAME[58:62] = pack_unsigned_long_int(gps_storage_info, STORAGE_IDX.DIR_SIZE)
        else:
            logger.warning("GPS Data process does not exist")

        ############ Payload fields ###########
        if DH.data_process_exists("payload"):
            payload_storage_info = DH.get_storage_info("payload")
            # PAYLOAD number of files
            cls._FRAME[62:66] = pack_unsigned_long_int(payload_storage_info, STORAGE_IDX.NUM_FILES)
            # PAYLOAD directory size
            cls._FRAME[66:70] = pack_unsigned_long_int(payload_storage_info, STORAGE_IDX.DIR_SIZE)
        else:
            logger.warning("Payload Data process does not exist")

        ############ Command fields ###########
        if DH.data_process_exists("cmd_logs"):
            cmd_logs_storage_info = DH.get_storage_info("cmd_logs")
            # Command logs number of files
            cls._FRAME[70:74] = pack_unsigned_long_int(cmd_logs_storage_info, STORAGE_IDX.NUM_FILES)
            # Command logs directory size
            cls._FRAME[74:78] = pack_unsigned_long_int(cmd_logs_storage_info, STORAGE_IDX.DIR_SIZE)
        else:
            logger.warning("Command logs Data process does not exist")

    @classmethod
    def pack_tm_payload(cls):
        pass

    @classmethod
    def change_tm_id_nominal(cls):
        """
        This will change the pack_tm_heartbeat() frame message ID to nominal.
        This is to help differentiate between a SAT_HEARTBEAT (nominally sent down)
        and one that was from REQUEST_TM_NOMINAL (requested by command)
        """
        cls._FRAME[0] = const(0x05) & 0xFF  # message ID
