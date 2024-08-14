"""

Telemetry packing for transmission

Each fixed-length LoRa Payload is structured as follows
MESSAGE_ID : 1 byte
SEQ_COUNT  : 2 bytes
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
from apps.telemetry.constants import ADCS_IDX, CDH_IDX, EPS_IDX, GPS_IDX, PAYLOAD_IDX, THERMAL_IDX
from apps.telemetry.helpers import (
    convert_float_to_fixed_point_hp,
    convert_float_to_fixed_point_lp,
    pack_signed_long_int,
    pack_signed_short_int,
    pack_unsigned_long_int,
    pack_unsigned_short_int,
)
from core.data_handler import DataHandler as DH


class TelemetryPacker:
    """
    Packs telemetry data for transmission
    """

    PACKET = bytearray(276)  # pre-allocated buffer for packing
    PACKET[0] = 0x01  # message ID
    PACKET[1] = 0x00  # sequence count
    PACKET[2] = 0x01  # sequence count
    PACKET[3] = 276  # packet length

    @classmethod
    def pack_telemetry(cls):

        ############ CDH fields ############
        cdh_data = DH.get_latest_data("cdh")

        # Time
        cls.PACKET[4:8] = pack_unsigned_long_int(cdh_data, CDH_IDX.TIME)

        # SC State
        cls.PACKET[8] = cdh_data[CDH_IDX.SC_STATE] & 0xFF

        # SD Usage
        cls.PACKET[9:13] = pack_unsigned_long_int(cdh_data, CDH_IDX.SD_USAGE)

        # Current RAM Usage
        cls.PACKET[13] = cdh_data[CDH_IDX.CURRENT_RAM_USAGE] & 0xFF

        # Reboot count
        cls.PACKET[14] = cdh_data[CDH_IDX.REBOOT_COUNT] & 0xFF

        # Watchdog Timer
        cls.PACKET[15] = cdh_data[CDH_IDX.WATCHDOG_TIMER] & 0xFF

        # HAL Bitflags
        cls.PACKET[16] = cdh_data[CDH_IDX.HAL_BITFLAGS] & 0xFF

        ############ EPS fields ############
        eps_data = DH.get_latest_data("eps")

        # Mainboard voltage
        cls.PACKET[17:19] = pack_signed_short_int(eps_data, EPS_IDX.MAINBOARD_VOLTAGE)

        # Mainboard current
        cls.PACKET[19:21] = pack_signed_short_int(eps_data, EPS_IDX.MAINBOARD_CURRENT)

        # Battery pack SOC
        cls.PACKET[21] = eps_data[EPS_IDX.BATTERY_PACK_REPORTED_SOC] & 0xFF

        # Battery pack capacity
        cls.PACKET[22:24] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_PACK_REPORTED_CAPACITY)

        # Battery pack current
        cls.PACKET[24:26] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_PACK_CURRENT)

        # Battery pack voltage
        cls.PACKET[26:28] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_PACK_VOLTAGE)

        # Battery pack midpoint voltage
        cls.PACKET[28:30] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_PACK_MIDPOINT_VOLTAGE)

        # Battery cycles
        cls.PACKET[30:32] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_CYCLES)

        # Battery pack TTE
        cls.PACKET[32:34] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_PACK_TTE)

        # Battery pack TTF
        cls.PACKET[34:36] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_PACK_TTF)

        # Battery time since power up
        cls.PACKET[36:38] = pack_signed_short_int(eps_data, EPS_IDX.BATTERY_TIME_SINCE_POWER_UP)

        # XP coil voltage
        cls.PACKET[38:40] = pack_signed_short_int(eps_data, EPS_IDX.XP_COIL_VOLTAGE)
        # XP coil current
        cls.PACKET[40:42] = pack_signed_short_int(eps_data, EPS_IDX.XP_COIL_CURRENT)

        # XM coil voltage
        cls.PACKET[42:44] = pack_signed_short_int(eps_data, EPS_IDX.XM_COIL_VOLTAGE)
        # XM coil current
        cls.PACKET[44:46] = pack_signed_short_int(eps_data, EPS_IDX.XM_COIL_CURRENT)

        # YP coil voltage
        cls.PACKET[46:48] = pack_signed_short_int(eps_data, EPS_IDX.YP_COIL_VOLTAGE)
        # YP coil current
        cls.PACKET[48:50] = pack_signed_short_int(eps_data, EPS_IDX.YP_COIL_CURRENT)

        # YM coil voltage
        cls.PACKET[50:52] = pack_signed_short_int(eps_data, EPS_IDX.YM_COIL_VOLTAGE)
        # YM coil current
        cls.PACKET[52:54] = pack_signed_short_int(eps_data, EPS_IDX.YM_COIL_CURRENT)

        # ZP coil voltage
        cls.PACKET[54:56] = pack_signed_short_int(eps_data, EPS_IDX.ZP_COIL_VOLTAGE)
        # ZP coil current
        cls.PACKET[56:58] = pack_signed_short_int(eps_data, EPS_IDX.ZP_COIL_CURRENT)

        # ZM coil voltage
        cls.PACKET[58:60] = pack_signed_short_int(eps_data, EPS_IDX.ZM_COIL_VOLTAGE)
        # ZM coil current
        cls.PACKET[60:62] = pack_signed_short_int(eps_data, EPS_IDX.ZM_COIL_CURRENT)

        # Jetson input voltage
        cls.PACKET[62:64] = pack_signed_short_int(eps_data, EPS_IDX.JETSON_INPUT_VOLTAGE)

        # Jetson input current
        cls.PACKET[64:66] = pack_signed_short_int(eps_data, EPS_IDX.JETSON_INPUT_CURRENT)

        # RF LDO output voltage
        cls.PACKET[66:68] = pack_signed_short_int(eps_data, EPS_IDX.RF_LDO_OUTPUT_VOLTAGE)

        # RF LDO output current
        cls.PACKET[68:70] = pack_signed_short_int(eps_data, EPS_IDX.RF_LDO_OUTPUT_CURRENT)

        # GPS voltage
        cls.PACKET[70:72] = pack_signed_short_int(eps_data, EPS_IDX.GPS_VOLTAGE)

        # GPS current
        cls.PACKET[72:74] = pack_signed_short_int(eps_data, EPS_IDX.GPS_CURRENT)

        # XP solar charge voltage
        cls.PACKET[74:76] = pack_signed_short_int(eps_data, EPS_IDX.XP_SOLAR_CHARGE_VOLTAGE)
        # XP solar charge current
        cls.PACKET[76:78] = pack_signed_short_int(eps_data, EPS_IDX.XP_SOLAR_CHARGE_CURRENT)

        # XM solar charge voltage
        cls.PACKET[78:80] = pack_signed_short_int(eps_data, EPS_IDX.XM_SOLAR_CHARGE_VOLTAGE)
        # XM solar charge current
        cls.PACKET[80:82] = pack_signed_short_int(eps_data, EPS_IDX.XM_SOLAR_CHARGE_CURRENT)

        # YP solar charge voltage
        cls.PACKET[82:84] = pack_signed_short_int(eps_data, EPS_IDX.YP_SOLAR_CHARGE_VOLTAGE)
        # YP solar charge current
        cls.PACKET[84:86] = pack_signed_short_int(eps_data, EPS_IDX.YP_SOLAR_CHARGE_CURRENT)

        # YM solar charge voltage
        cls.PACKET[86:88] = pack_signed_short_int(eps_data, EPS_IDX.YM_SOLAR_CHARGE_VOLTAGE)
        # YM solar charge current
        cls.PACKET[88:90] = pack_signed_short_int(eps_data, EPS_IDX.YM_SOLAR_CHARGE_CURRENT)

        # ZP solar charge voltage
        cls.PACKET[90:92] = pack_signed_short_int(eps_data, EPS_IDX.ZP_SOLAR_CHARGE_VOLTAGE)
        # ZP solar charge current
        cls.PACKET[92:94] = pack_signed_short_int(eps_data, EPS_IDX.ZP_SOLAR_CHARGE_CURRENT)

        # ZM solar charge voltage
        cls.PACKET[94:96] = pack_signed_short_int(eps_data, EPS_IDX.ZM_SOLAR_CHARGE_VOLTAGE)
        # ZM solar charge current
        cls.PACKET[96:98] = pack_signed_short_int(eps_data, EPS_IDX.ZM_SOLAR_CHARGE_CURRENT)

        ############ ADCS fields ############
        adcs_data = DH.get_latest_data("adcs")

        # ADCS state
        cls.PACKET[98] = adcs_data[ADCS_IDX.ADCS_STATE] & 0xFF

        # Gyro X
        cls.PACKET[99:103] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.GYRO_X])
        # Gyro Y
        cls.PACKET[103:107] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.GYRO_Y])
        # Gyro Z
        cls.PACKET[107:111] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.GYRO_Z])

        # Magnetometer X
        cls.PACKET[111:115] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.MAGNETOMETER_X])
        # Magnetometer Y
        cls.PACKET[115:119] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.MAGNETOMETER_Y])
        # Magnetometer Z
        cls.PACKET[119:123] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.MAGNETOMETER_Z])

        # Sun status
        cls.PACKET[123] = adcs_data[ADCS_IDX.SUN_STATUS] & 0xFF

        # Sun vector X
        cls.PACKET[124:128] = pack_signed_long_int(adcs_data, ADCS_IDX.SUN_VEC_X)
        # Sun vector Y
        cls.PACKET[128:132] = pack_signed_long_int(adcs_data, ADCS_IDX.SUN_VEC_Y)
        # Sun vector Z
        cls.PACKET[132:136] = pack_signed_long_int(adcs_data, ADCS_IDX.SUN_VEC_Z)
        # Eclipse bool
        cls.PACKET[136] = adcs_data[ADCS_IDX.ECLIPSE] & 0xFF
        # Light sensor X+
        cls.PACKET[137:141] = pack_unsigned_long_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_XP)
        # Light sensor X-
        cls.PACKET[141:145] = pack_unsigned_long_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_XM)
        # Light sensor Y+
        cls.PACKET[145:149] = pack_unsigned_long_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_YP)
        # Light sensor Y-
        cls.PACKET[149:153] = pack_unsigned_long_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_YM)
        # Light sensor Z+ 1
        cls.PACKET[153:157] = pack_unsigned_long_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZP1)
        # Light sensor Z+ 2
        cls.PACKET[157:161] = pack_unsigned_long_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZP2)
        # Light sensor Z+ 3
        cls.PACKET[161:165] = pack_unsigned_long_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZP3)
        # Light sensor Z+ 4
        cls.PACKET[165:169] = pack_unsigned_long_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZP4)
        # Light sensor Z-
        cls.PACKET[169:173] = pack_unsigned_long_int(adcs_data, ADCS_IDX.LIGHT_SENSOR_ZM)

        # XP coil status
        cls.PACKET[174] = adcs_data[ADCS_IDX.XP_COIL_STATUS] & 0xFF
        # XM coil status
        cls.PACKET[175] = adcs_data[ADCS_IDX.XM_COIL_STATUS] & 0xFF
        # YP coil status
        cls.PACKET[176] = adcs_data[ADCS_IDX.YP_COIL_STATUS] & 0xFF
        # YM coil status
        cls.PACKET[177] = adcs_data[ADCS_IDX.YM_COIL_STATUS] & 0xFF
        # ZP coil status
        cls.PACKET[178] = adcs_data[ADCS_IDX.ZP_COIL_STATUS] & 0xFF
        # ZM coil status
        cls.PACKET[179] = adcs_data[ADCS_IDX.ZM_COIL_STATUS] & 0xFF

        # Coarse attitude QW
        cls.PACKET[180:184] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.COARSE_ATTITUDE_QW])
        # Coarse attitude QX
        cls.PACKET[184:188] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.COARSE_ATTITUDE_QX])
        # Coarse attitude QY
        cls.PACKET[188:192] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.COARSE_ATTITUDE_QY])
        # Coarse attitude QZ
        cls.PACKET[192:196] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.COARSE_ATTITUDE_QZ])

        # Star tracker status
        cls.PACKET[197] = adcs_data[ADCS_IDX.STAR_TRACKER_STATUS] & 0xFF

        # Star tracker attitude QW
        cls.PACKET[198:202] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.STAR_TRACKER_ATTITUDE_QW])
        # Star tracker attitude QX
        cls.PACKET[202:206] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.STAR_TRACKER_ATTITUDE_QX])
        # Star tracker attitude QY
        cls.PACKET[206:210] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.STAR_TRACKER_ATTITUDE_QY])
        # Star tracker attitude QZ
        cls.PACKET[210:214] = convert_float_to_fixed_point_hp(adcs_data[ADCS_IDX.STAR_TRACKER_ATTITUDE_QZ])

        ############ GPS fields ############
        gps_data = DH.get_latest_data("gps")

        # message ID
        cls.PACKET[215] = gps_data[GPS_IDX.GPS_MESSAGE_ID] & 0xFF
        # fix mode
        cls.PACKET[216] = gps_data[GPS_IDX.GPS_FIX_MODE] & 0xFF
        # number of SV
        cls.PACKET[217] = gps_data[GPS_IDX.GPS_NUMBER_OF_SV] & 0xFF
        # GNSS week
        cls.PACKET[218:220] = pack_unsigned_short_int(gps_data, GPS_IDX.GPS_GNSS_WEEK)
        # GNSS TOW
        cls.PACKET[220:224] = pack_unsigned_long_int(gps_data, GPS_IDX.GPS_GNSS_TOW)
        # latitude
        cls.PACKET[224:228] = pack_signed_long_int(gps_data, GPS_IDX.GPS_LATITUDE)
        # longitude
        cls.PACKET[228:232] = pack_signed_long_int(gps_data, GPS_IDX.GPS_LONGITUDE)
        # ellipsoid altitude
        cls.PACKET[232:236] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ELLIPSOID_ALT)
        # mean sea level altitude
        cls.PACKET[236:240] = pack_signed_long_int(gps_data, GPS_IDX.GPS_MEAN_SEA_LVL_ALT)

        # ECEF X
        cls.PACKET[240:244] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_X)
        # ECEF Y
        cls.PACKET[244:248] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_Y)
        # ECEF Z
        cls.PACKET[248:252] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_Z)
        # ECEF VX
        cls.PACKET[252:256] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_VX)
        # ECEF VY
        cls.PACKET[256:260] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_VY)
        # ECEF VZ
        cls.PACKET[260:264] = pack_signed_long_int(gps_data, GPS_IDX.GPS_ECEF_VZ)

        ############ Thermal fields ############
        thermal_data = DH.get_latest_data("thermal")

        # IMU temperature
        cls.PACKET[264:268] = pack_unsigned_short_int(thermal_data, THERMAL_IDX.IMU_TEMPERATURE)
        # CPU temperature
        cls.PACKET[268:272] = pack_unsigned_short_int(thermal_data, THERMAL_IDX.CPU_TEMPERATURE)
        # Battery temperature
        cls.PACKET[272:276] = pack_unsigned_short_int(thermal_data, THERMAL_IDX.BATTERY_PACK_TEMPERATURE)

        ############ Payload fields ############
        # TODO
