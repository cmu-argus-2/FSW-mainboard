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
    def pack_tm_heartbeat(cls):

        if not cls._TM_AVAILABLE:
            cls._TM_AVAILABLE = True

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
                # Mainboard voltage
                cls._FRAME[18:20] = pack_signed_short_int(eps_data, EPS_IDX.MAINBOARD_VOLTAGE)
                # Mainboard current
                cls._FRAME[20:22] = pack_signed_short_int(eps_data, EPS_IDX.MAINBOARD_CURRENT)
                # Battery pack SOC
                cls._FRAME[22] = eps_data[EPS_IDX.BATTERY_PACK_REPORTED_SOC] & 0xFF
                # Battery pack capacity
                cls._FRAME[23:25] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_PACK_REPORTED_CAPACITY)
                # Battery pack current
                cls._FRAME[25:27] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_PACK_CURRENT)
                # Battery pack voltage
                cls._FRAME[27:29] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_PACK_VOLTAGE)
                # Battery pack midpoint voltage
                cls._FRAME[29:31] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_PACK_MIDPOINT_VOLTAGE)
                # Battery cycles
                cls._FRAME[31:33] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_CYCLES)
                # Battery pack TTE
                cls._FRAME[33:35] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_PACK_TTE)
                # Battery pack TTF
                cls._FRAME[35:37] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_PACK_TTF)
                # Battery time since power up
                cls._FRAME[37:39] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_TIME_SINCE_POWER_UP)

                # XP coil voltage
                cls._FRAME[39:41] = pack_signed_short_int(eps_data, EPS_IDX.XP_COIL_VOLTAGE)
                # XP coil current
                cls._FRAME[41:43] = pack_signed_short_int(eps_data, EPS_IDX.XP_COIL_CURRENT)
                # XM coil voltage
                cls._FRAME[43:45] = pack_signed_short_int(eps_data, EPS_IDX.XM_COIL_VOLTAGE)
                # XM coil current
                cls._FRAME[45:47] = pack_signed_short_int(eps_data, EPS_IDX.XM_COIL_CURRENT)
                # YP coil voltage
                cls._FRAME[47:49] = pack_signed_short_int(eps_data, EPS_IDX.YP_COIL_VOLTAGE)
                # YP coil current
                cls._FRAME[49:51] = pack_signed_short_int(eps_data, EPS_IDX.YP_COIL_CURRENT)
                # YM coil voltage
                cls._FRAME[51:53] = pack_signed_short_int(eps_data, EPS_IDX.YM_COIL_VOLTAGE)
                # YM coil current
                cls._FRAME[53:55] = pack_signed_short_int(eps_data, EPS_IDX.YM_COIL_CURRENT)
                # ZP coil voltage
                cls._FRAME[55:57] = pack_signed_short_int(eps_data, EPS_IDX.ZP_COIL_VOLTAGE)
                # ZP coil current
                cls._FRAME[57:59] = pack_signed_short_int(eps_data, EPS_IDX.ZP_COIL_CURRENT)
                # ZM coil voltage
                cls._FRAME[59:61] = pack_signed_short_int(eps_data, EPS_IDX.ZM_COIL_VOLTAGE)
                # ZM coil current
                cls._FRAME[61:63] = pack_signed_short_int(eps_data, EPS_IDX.ZM_COIL_CURRENT)

                # Jetson input voltage
                cls._FRAME[63:65] = pack_signed_short_int(eps_data, EPS_IDX.JETSON_INPUT_VOLTAGE)
                # Jetson input current
                cls._FRAME[65:67] = pack_signed_short_int(eps_data, EPS_IDX.JETSON_INPUT_CURRENT)

                # RF LDO output voltage
                cls._FRAME[67:69] = pack_signed_short_int(eps_data, EPS_IDX.RF_LDO_OUTPUT_VOLTAGE)
                # RF LDO output current
                cls._FRAME[69:71] = pack_signed_short_int(eps_data, EPS_IDX.RF_LDO_OUTPUT_CURRENT)

                # GPS voltage
                cls._FRAME[71:73] = pack_signed_short_int(eps_data, EPS_IDX.GPS_VOLTAGE)
                # GPS current
                cls._FRAME[73:75] = pack_signed_short_int(eps_data, EPS_IDX.GPS_CURRENT)

                # XP solar charge voltage
                cls._FRAME[75:77] = pack_signed_short_int(eps_data, EPS_IDX.XP_SOLAR_CHARGE_VOLTAGE)
                # XP solar charge current
                cls._FRAME[77:79] = pack_signed_short_int(eps_data, EPS_IDX.XP_SOLAR_CHARGE_CURRENT)
                # XM solar charge voltage
                cls._FRAME[79:81] = pack_signed_short_int(eps_data, EPS_IDX.XM_SOLAR_CHARGE_VOLTAGE)
                # XM solar charge current
                cls._FRAME[81:83] = pack_signed_short_int(eps_data, EPS_IDX.XM_SOLAR_CHARGE_CURRENT)
                # YP solar charge voltage
                cls._FRAME[83:85] = pack_signed_short_int(eps_data, EPS_IDX.YP_SOLAR_CHARGE_VOLTAGE)
                # YP solar charge current
                cls._FRAME[85:87] = pack_signed_short_int(eps_data, EPS_IDX.YP_SOLAR_CHARGE_CURRENT)
                # YM solar charge voltage
                cls._FRAME[87:89] = pack_signed_short_int(eps_data, EPS_IDX.YM_SOLAR_CHARGE_VOLTAGE)
                # YM solar charge current
                cls._FRAME[89:91] = pack_signed_short_int(eps_data, EPS_IDX.YM_SOLAR_CHARGE_CURRENT)
                # ZP solar charge voltage
                cls._FRAME[91:93] = pack_signed_short_int(eps_data, EPS_IDX.ZP_SOLAR_CHARGE_VOLTAGE)
                # ZP solar charge current
                cls._FRAME[93:95] = pack_signed_short_int(eps_data, EPS_IDX.ZP_SOLAR_CHARGE_CURRENT)
                # ZM solar charge voltage
                cls._FRAME[95:97] = pack_signed_short_int(eps_data, EPS_IDX.ZM_SOLAR_CHARGE_VOLTAGE)
                # ZM solar charge current
                cls._FRAME[97:99] = pack_signed_short_int(eps_data, EPS_IDX.ZM_SOLAR_CHARGE_CURRENT)

            else:
                logger.warning("No latest EPS data available")
        else:
            logger.warning("No EPS data available")

        ############ ADCS fields ############
        if DH.data_process_exists("adcs"):

            adcs_data = DH.get_latest_data("adcs")

            if adcs_data:
                # ADCS state
                cls._FRAME[99] = adcs_data[ADCS_IDX.MODE] & 0xFF

                # Gyro X
                cls._FRAME[100:104] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.GYRO_X])
                # Gyro Y
                cls._FRAME[104:108] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.GYRO_Y])
                # Gyro Z
                cls._FRAME[108:112] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.GYRO_Z])

                # Magnetometer X
                cls._FRAME[112:116] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.MAG_X])
                # Magnetometer Y
                cls._FRAME[116:120] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.MAG_Y])
                # Magnetometer Z
                cls._FRAME[120:124] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.MAG_Z])

                # Sun status
                cls._FRAME[124] = adcs_data[ADCS_IDX.SUN_STATUS] & 0xFF
                # Sun vector X
                cls._FRAME[125:129] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.SUN_VEC_X])
                # Sun vector Y
                cls._FRAME[129:133] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.SUN_VEC_Y])
                # Sun vector Z
                cls._FRAME[133:137] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.SUN_VEC_Z])
                # Eclipse bool
                cls._FRAME[137] = adcs_data[ADCS_IDX.ECLIPSE] & 0xFF
                # Light sensor X+
                cls._FRAME[138:140] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_XP)
                # Light sensor X-
                cls._FRAME[140:142] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_XM)
                # Light sensor Y+
                cls._FRAME[142:144] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_YP)
                # Light sensor Y-
                cls._FRAME[144:146] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_YM)
                # Light sensor Z+ 1
                cls._FRAME[146:148] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZP1)
                # Light sensor Z+ 2
                cls._FRAME[148:150] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZP2)
                # Light sensor Z+ 3
                cls._FRAME[150:152] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZP3)
                # Light sensor Z+ 4
                cls._FRAME[152:154] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZP4)
                # Light sensor Z-
                cls._FRAME[154:156] = pack_unsigned_short_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZM)

                # XP coil status
                cls._FRAME[156] = adcs_data[ADCS_IDX.XP_COIL_STATUS] & 0xFF
                # XM coil status
                cls._FRAME[157] = adcs_data[ADCS_IDX.XM_COIL_STATUS] & 0xFF
                # YP coil status
                cls._FRAME[158] = adcs_data[ADCS_IDX.YP_COIL_STATUS] & 0xFF
                # YM coil status
                cls._FRAME[159] = adcs_data[ADCS_IDX.YM_COIL_STATUS] & 0xFF
                # ZP coil status
                cls._FRAME[160] = adcs_data[ADCS_IDX.ZP_COIL_STATUS] & 0xFF
                # ZM coil status
                cls._FRAME[161] = adcs_data[ADCS_IDX.ZM_COIL_STATUS] & 0xFF

                # Coarse attitude QW
                cls._FRAME[162:166] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.COARSE_ATTITUDE_QW])
                # Coarse attitude QX
                cls._FRAME[166:170] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.COARSE_ATTITUDE_QX])
                # Coarse attitude QY
                cls._FRAME[170:174] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.COARSE_ATTITUDE_QY])
                # Coarse attitude QZ
                cls._FRAME[174:178] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.COARSE_ATTITUDE_QZ])

            else:
                logger.warning("No latest ADCS data available")
        else:
            logger.warning("No ADCS data available")

        ############ GPS fields ############
        if DH.data_process_exists("gps"):

            gps_data = DH.get_latest_data("gps")

            if gps_data:
                # TODO: fix indices (compress TM frame)

                # message ID
                cls._FRAME[179] = gps_data[GPS_IDX.GPS_MESSAGE_ID] & 0xFF
                # fix mode
                cls._FRAME[180] = gps_data[GPS_IDX.GPS_FIX_MODE] & 0xFF
                # number of SV
                cls._FRAME[181] = gps_data[GPS_IDX.GPS_NUMBER_OF_SV] & 0xFF
                # GNSS week
                cls._FRAME[182:184] = pack_unsigned_short_int(gps_data, GPS_IDX.GPS_GNSS_WEEK)
                # GNSS TOW
                cls._FRAME[184:188] = pack_unsigned_long_int(gps_data, GPS_IDX.GPS_GNSS_TOW)
                # latitude
                cls._FRAME[188:192] = pack_signed_long_int(gps_data, GPS_IDX.GPS_LATITUDE)
                # longitude
                cls._FRAME[192:196] = pack_signed_long_int(gps_data, GPS_IDX.GPS_LONGITUDE)
                # ellipsoid altitude
                cls._FRAME[196:200] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ELLIPSOID_ALT)
                # mean sea level altitude
                cls._FRAME[200:204] = pack_signed_long_int(gps_data, GPS_IDX.GPS_MEAN_SEA_LVL_ALT)
                # ECEF X
                cls._FRAME[204:208] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_X)
                # ECEF Y
                cls._FRAME[208:212] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_Y)
                # ECEF Z
                cls._FRAME[212:216] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_Z)
                # ECEF VX
                cls._FRAME[216:220] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_VX)
                # ECEF VY
                cls._FRAME[220:224] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_VY)
                # ECEF VZ
                cls._FRAME[224:228] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_VZ)
            else:
                logger.warning("No latest GPS data available")
        else:
            logger.warning("No GPS data available")

        ############ Thermal fields ############

        if DH.data_process_exists("thermal"):
            thermal_data = DH.get_latest_data("thermal")
            if thermal_data:
                # IMU temperature
                cls._FRAME[228:230] = pack_unsigned_short_int(thermal_data, THERMAL_IDX.IMU_TEMPERATURE)
                # CPU temperature
                cls._FRAME[230:232] = pack_unsigned_short_int(thermal_data, THERMAL_IDX.CPU_TEMPERATURE)
                # Battery temperature
                cls._FRAME[232:234] = pack_unsigned_short_int(thermal_data, THERMAL_IDX.BATTERY_PACK_TEMPERATURE)
            else:
                logger.warning("No latest Thermal data available")
        else:
            logger.warning("No Thermal data available")

        cls._FRAME[:] = bytearray(cls._FRAME[:])
        gc.collect()

        ############ Payload status fields ############
        # TODO

        return True

    @classmethod
    def pack_tm_hal(cls):
        # TODO: CDH, HAL status, error codes, EPS
        pass

    @classmethod
    def pack_tm_storage(cls):
        # TODO: CDH, DH snapshot
        pass

    @classmethod
    def pack_tm_payload(cls):
        pass
