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
from core.data_handler import DataHandler as DH


def pack_4_bytes(data, idx):
    """
    Packs 4-byte into a bytearray
    """
    return [(data[idx] >> 24) & 0xFF, (data[idx] >> 16) & 0xFF, (data[idx] >> 8) & 0xFF, data[idx] & 0xFF]


class TelemetryPacker:
    """
    Packs telemetry data for transmission
    """

    PACKET = bytearray(256)  # pre-allocated buffer for packing
    PACKET[0] = 0x01  # message ID
    PACKET[1] = 0x00  # sequence count
    PACKET[2] = 0x01  # sequence count
    PACKET[3] = 252  # packet length

    @classmethod
    def pack_telemetry(cls):

        ############ CDH fields ############
        cdh_data = DH.get_latest_data("cdh")

        # Time
        time = cdh_data[CDH_IDX.TIME]
        cls.PACKET[4] = (time >> 24) & 0xFF
        cls.PACKET[5] = (time >> 16) & 0xFF
        cls.PACKET[6] = (time >> 8) & 0xFF
        cls.PACKET[7] = time & 0xFF

        # SC State
        cls.PACKET[8] = cdh_data[CDH_IDX.SC_STATE] & 0xFF

        # SD Usage
        sd_usage = cdh_data[CDH_IDX.SD_USAGE]
        cls.PACKET[9] = (sd_usage >> 24) & 0xFF
        cls.PACKET[10] = (sd_usage >> 16) & 0xFF
        cls.PACKET[11] = (sd_usage >> 8) & 0xFF
        cls.PACKET[12] = sd_usage & 0xFF

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
        cls.PACKET[17] = (eps_data[EPS_IDX.MAINBOARD_VOLTAGE] >> 8) & 0xFF
        cls.PACKET[18] = eps_data[EPS_IDX.MAINBOARD_VOLTAGE] & 0xFF

        # Mainboard current
        cls.PACKET[19] = (eps_data[EPS_IDX.MAINBOARD_CURRENT] >> 8) & 0xFF
        cls.PACKET[20] = eps_data[EPS_IDX.MAINBOARD_CURRENT] & 0xFF

        # Battery pack SOC
        cls.PACKET[21] = eps_data[EPS_IDX.BATTERY_PACK_REPORTED_SOC] & 0xFF

        # Battery pack capacity
        cls.PACKET[22] = (eps_data[EPS_IDX.BATTERY_PACK_REPORTED_CAPACITY] >> 8) & 0xFF
        cls.PACKET[23] = eps_data[EPS_IDX.BATTERY_PACK_REPORTED_CAPACITY] & 0xFF

        # Battery pack current
        cls.PACKET[24] = (eps_data[EPS_IDX.BATTERY_PACK_CURRENT] >> 8) & 0xFF
        cls.PACKET[25] = eps_data[EPS_IDX.BATTERY_PACK_CURRENT] & 0xFF

        # Battery pack voltage
        cls.PACKET[26] = (eps_data[EPS_IDX.BATTERY_PACK_VOLTAGE] >> 8) & 0xFF
        cls.PACKET[27] = eps_data[EPS_IDX.BATTERY_PACK_VOLTAGE] & 0xFF

        # Battery pack midpoint voltage
        cls.PACKET[28] = (eps_data[EPS_IDX.BATTERY_PACK_MIDPOINT_VOLTAGE] >> 8) & 0xFF
        cls.PACKET[29] = eps_data[EPS_IDX.BATTERY_PACK_MIDPOINT_VOLTAGE] & 0xFF

        # Battery cycles
        cls.PACKET[30] = (eps_data[EPS_IDX.BATTERY_CYCLES] >> 8) & 0xFF
        cls.PACKET[31] = eps_data[EPS_IDX.BATTERY_CYCLES] & 0xFF

        # Battery pack TTE
        cls.PACKET[32] = (eps_data[EPS_IDX.BATTERY_PACK_TTE] >> 8) & 0xFF
        cls.PACKET[33] = eps_data[EPS_IDX.BATTERY_PACK_TTE] & 0xFF

        # Battery pack TTF
        cls.PACKET[34] = (eps_data[EPS_IDX.BATTERY_PACK_TTF] >> 8) & 0xFF
        cls.PACKET[35] = eps_data[EPS_IDX.BATTERY_PACK_TTF] & 0xFF

        # Battery time since power up
        cls.PACKET[36] = (eps_data[EPS_IDX.BATTERY_TIME_SINCE_POWER_UP] >> 8) & 0xFF
        cls.PACKET[37] = eps_data[EPS_IDX.BATTERY_TIME_SINCE_POWER_UP] & 0xFF

        # XP coil voltage
        cls.PACKET[38] = (eps_data[EPS_IDX.XP_COIL_VOLTAGE] >> 8) & 0xFF
        cls.PACKET[39] = eps_data[EPS_IDX.XP_COIL_VOLTAGE] & 0xFF
        # XP coil current
        cls.PACKET[40] = (eps_data[EPS_IDX.XP_COIL_CURRENT] >> 8) & 0xFF
        cls.PACKET[41] = eps_data[EPS_IDX.XP_COIL_CURRENT] & 0xFF

        # XM coil voltage
        cls.PACKET[42] = (eps_data[EPS_IDX.XM_COIL_VOLTAGE] >> 8) & 0xFF
        cls.PACKET[43] = eps_data[EPS_IDX.XM_COIL_VOLTAGE] & 0xFF
        # XM coil current
        cls.PACKET[44] = (eps_data[EPS_IDX.XM_COIL_CURRENT] >> 8) & 0xFF
        cls.PACKET[45] = eps_data[EPS_IDX.XM_COIL_CURRENT] & 0xFF

        # YP coil voltage
        cls.PACKET[46] = (eps_data[EPS_IDX.YP_COIL_VOLTAGE] >> 8) & 0xFF
        cls.PACKET[47] = eps_data[EPS_IDX.YP_COIL_VOLTAGE] & 0xFF
        # YP coil current
        cls.PACKET[48] = (eps_data[EPS_IDX.YP_COIL_CURRENT] >> 8) & 0xFF
        cls.PACKET[49] = eps_data[EPS_IDX.YP_COIL_CURRENT] & 0xFF

        # YM coil voltage
        cls.PACKET[50] = (eps_data[EPS_IDX.YM_COIL_VOLTAGE] >> 8) & 0xFF
        cls.PACKET[51] = eps_data[EPS_IDX.YM_COIL_VOLTAGE] & 0xFF
        # YM coil current
        cls.PACKET[52] = (eps_data[EPS_IDX.YM_COIL_CURRENT] >> 8) & 0xFF
        cls.PACKET[53] = eps_data[EPS_IDX.YM_COIL_CURRENT] & 0xFF

        # ZP coil voltage
        cls.PACKET[54] = (eps_data[EPS_IDX.ZP_COIL_VOLTAGE] >> 8) & 0xFF
        cls.PACKET[55] = eps_data[EPS_IDX.ZP_COIL_VOLTAGE] & 0xFF
        # ZP coil current
        cls.PACKET[56] = (eps_data[EPS_IDX.ZP_COIL_CURRENT] >> 8) & 0xFF
        cls.PACKET[57] = eps_data[EPS_IDX.ZP_COIL_CURRENT] & 0xFF

        # ZM coil voltage
        cls.PACKET[58] = (eps_data[EPS_IDX.ZM_COIL_VOLTAGE] >> 8) & 0xFF
        cls.PACKET[59] = eps_data[EPS_IDX.ZM_COIL_VOLTAGE] & 0xFF
        # ZM coil current
        cls.PACKET[60] = (eps_data[EPS_IDX.ZM_COIL_CURRENT] >> 8) & 0xFF
        cls.PACKET[61] = eps_data[EPS_IDX.ZM_COIL_CURRENT] & 0xFF

        # Jetson input voltage
        cls.PACKET[62] = (eps_data[EPS_IDX.JETSON_INPUT_VOLTAGE] >> 8) & 0xFF
        cls.PACKET[63] = eps_data[EPS_IDX.JETSON_INPUT_VOLTAGE] & 0xFF

        # Jetson input current
        cls.PACKET[64] = (eps_data[EPS_IDX.JETSON_INPUT_CURRENT] >> 8) & 0xFF
        cls.PACKET[65] = eps_data[EPS_IDX.JETSON_INPUT_CURRENT] & 0xFF

        # RF LDO output voltage
        cls.PACKET[66] = (eps_data[EPS_IDX.RF_LDO_OUTPUT_VOLTAGE] >> 8) & 0xFF
        cls.PACKET[67] = eps_data[EPS_IDX.RF_LDO_OUTPUT_VOLTAGE] & 0xFF

        # RF LDO output current
        cls.PACKET[68] = (eps_data[EPS_IDX.RF_LDO_OUTPUT_CURRENT] >> 8) & 0xFF
        cls.PACKET[69] = eps_data[EPS_IDX.RF_LDO_OUTPUT_CURRENT] & 0xFF

        # GPS voltage
        cls.PACKET[70] = (eps_data[EPS_IDX.GPS_VOLTAGE] >> 8) & 0xFF
        cls.PACKET[71] = eps_data[EPS_IDX.GPS_VOLTAGE] & 0xFF

        # GPS current
        cls.PACKET[72] = (eps_data[EPS_IDX.GPS_CURRENT] >> 8) & 0xFF
        cls.PACKET[73] = eps_data[EPS_IDX.GPS_CURRENT] & 0xFF

        # XP solar charge voltage
        cls.PACKET[74] = (eps_data[EPS_IDX.XP_SOLAR_CHARGE_VOLTAGE] >> 8) & 0xFF
        cls.PACKET[75] = eps_data[EPS_IDX.XP_SOLAR_CHARGE_VOLTAGE] & 0xFF
        # XP solar charge current
        cls.PACKET[76] = (eps_data[EPS_IDX.XP_SOLAR_CHARGE_CURRENT] >> 8) & 0xFF
        cls.PACKET[77] = eps_data[EPS_IDX.XP_SOLAR_CHARGE_CURRENT] & 0xFF

        # XM solar charge voltage
        cls.PACKET[78] = (eps_data[EPS_IDX.XM_SOLAR_CHARGE_VOLTAGE] >> 8) & 0xFF
        cls.PACKET[79] = eps_data[EPS_IDX.XM_SOLAR_CHARGE_VOLTAGE] & 0xFF
        # XM solar charge current
        cls.PACKET[80] = (eps_data[EPS_IDX.XM_SOLAR_CHARGE_CURRENT] >> 8) & 0xFF
        cls.PACKET[81] = eps_data[EPS_IDX.XM_SOLAR_CHARGE_CURRENT] & 0xFF

        # YP solar charge voltage
        cls.PACKET[82] = (eps_data[EPS_IDX.YP_SOLAR_CHARGE_VOLTAGE] >> 8) & 0xFF
        cls.PACKET[83] = eps_data[EPS_IDX.YP_SOLAR_CHARGE_VOLTAGE] & 0xFF
        # YP solar charge current
        cls.PACKET[84] = (eps_data[EPS_IDX.YP_SOLAR_CHARGE_CURRENT] >> 8) & 0xFF
        cls.PACKET[85] = eps_data[EPS_IDX.YP_SOLAR_CHARGE_CURRENT] & 0xFF

        # YM solar charge voltage
        cls.PACKET[86] = (eps_data[EPS_IDX.YM_SOLAR_CHARGE_VOLTAGE] >> 8) & 0xFF
        cls.PACKET[87] = eps_data[EPS_IDX.YM_SOLAR_CHARGE_VOLTAGE] & 0xFF
        # YM solar charge current
        cls.PACKET[88] = (eps_data[EPS_IDX.YM_SOLAR_CHARGE_CURRENT] >> 8) & 0xFF
        cls.PACKET[89] = eps_data[EPS_IDX.YM_SOLAR_CHARGE_CURRENT] & 0xFF

        # ZP solar charge voltage
        cls.PACKET[90] = (eps_data[EPS_IDX.ZP_SOLAR_CHARGE_VOLTAGE] >> 8) & 0xFF
        cls.PACKET[91] = eps_data[EPS_IDX.ZP_SOLAR_CHARGE_VOLTAGE] & 0xFF
        # ZP solar charge current
        cls.PACKET[92] = (eps_data[EPS_IDX.ZP_SOLAR_CHARGE_CURRENT] >> 8) & 0xFF
        cls.PACKET[93] = eps_data[EPS_IDX.ZP_SOLAR_CHARGE_CURRENT] & 0xFF

        # ZM solar charge voltage
        cls.PACKET[94] = (eps_data[EPS_IDX.ZM_SOLAR_CHARGE_VOLTAGE] >> 8) & 0xFF
        cls.PACKET[95] = eps_data[EPS_IDX.ZM_SOLAR_CHARGE_VOLTAGE] & 0xFF
        # ZM solar charge current
        cls.PACKET[96] = (eps_data[EPS_IDX.ZM_SOLAR_CHARGE_CURRENT] >> 8) & 0xFF
        cls.PACKET[97] = eps_data[EPS_IDX.ZM_SOLAR_CHARGE_CURRENT] & 0xFF

        ############ ADCS fields ############
        adcs_data = DH.get_latest_data("adcs")

        # ADCS state
        cls.PACKET[98] = adcs_data[ADCS_IDX.ADCS_STATE] & 0xFF

        # Gyro X
        cls.PACKET[99] = (adcs_data[ADCS_IDX.GYRO_X] >> 24) & 0xFF
        cls.PACKET[100] = (adcs_data[ADCS_IDX.GYRO_X] >> 16) & 0xFF
        cls.PACKET[101] = (adcs_data[ADCS_IDX.GYRO_X] >> 8) & 0xFF
        cls.PACKET[102] = adcs_data[ADCS_IDX.GYRO_X] & 0xFF
        # Gyro Y
        cls.PACKET[103] = (adcs_data[ADCS_IDX.GYRO_Y] >> 24) & 0xFF
        cls.PACKET[104] = (adcs_data[ADCS_IDX.GYRO_Y] >> 16) & 0xFF
        cls.PACKET[105] = (adcs_data[ADCS_IDX.GYRO_Y] >> 8) & 0xFF
        cls.PACKET[106] = adcs_data[ADCS_IDX.GYRO_Y] & 0xFF
        # Gyro Z
        cls.PACKET[107] = (adcs_data[ADCS_IDX.GYRO_Z] >> 24) & 0xFF
        cls.PACKET[108] = (adcs_data[ADCS_IDX.GYRO_Z] >> 16) & 0xFF
        cls.PACKET[109] = (adcs_data[ADCS_IDX.GYRO_Z] >> 8) & 0xFF
        cls.PACKET[110] = adcs_data[ADCS_IDX.GYRO_Z] & 0xFF

        # Magnetometer X
        cls.PACKET[111] = (adcs_data[ADCS_IDX.MAGNETOMETER_X] >> 24) & 0xFF
        cls.PACKET[112] = (adcs_data[ADCS_IDX.MAGNETOMETER_X] >> 16) & 0xFF
        cls.PACKET[113] = (adcs_data[ADCS_IDX.MAGNETOMETER_X] >> 8) & 0xFF
        cls.PACKET[114] = adcs_data[ADCS_IDX.MAGNETOMETER_X] & 0xFF
        # Magnetometer Y
        cls.PACKET[115] = (adcs_data[ADCS_IDX.MAGNETOMETER_Y] >> 24) & 0xFF
        cls.PACKET[116] = (adcs_data[ADCS_IDX.MAGNETOMETER_Y] >> 16) & 0xFF
        cls.PACKET[117] = (adcs_data[ADCS_IDX.MAGNETOMETER_Y] >> 8) & 0xFF
        cls.PACKET[118] = adcs_data[ADCS_IDX.MAGNETOMETER_Y] & 0xFF
        # Magnetometer Z
        cls.PACKET[119] = (adcs_data[ADCS_IDX.MAGNETOMETER_Z] >> 24) & 0xFF
        cls.PACKET[120] = (adcs_data[ADCS_IDX.MAGNETOMETER_Z] >> 16) & 0xFF
        cls.PACKET[121] = (adcs_data[ADCS_IDX.MAGNETOMETER_Z] >> 8) & 0xFF
        cls.PACKET[122] = adcs_data[ADCS_IDX.MAGNETOMETER_Z] & 0xFF

        # Sun status
        cls.PACKET[123] = adcs_data[ADCS_IDX.SUN_STATUS] & 0xFF

        # Sun vector X
        cls.PACKET[124] = (adcs_data[ADCS_IDX.SUN_VEC_X] >> 24) & 0xFF
        cls.PACKET[125] = (adcs_data[ADCS_IDX.SUN_VEC_X] >> 16) & 0xFF
        cls.PACKET[126] = (adcs_data[ADCS_IDX.SUN_VEC_X] >> 8) & 0xFF
        cls.PACKET[127] = adcs_data[ADCS_IDX.SUN_VEC_X] & 0xFF
        # Sun vector Y
        cls.PACKET[125] = (adcs_data[ADCS_IDX.SUN_VEC_Y] >> 24) & 0xFF
        cls.PACKET[126] = (adcs_data[ADCS_IDX.SUN_VEC_Y] >> 16) & 0xFF
        cls.PACKET[127] = (adcs_data[ADCS_IDX.SUN_VEC_Y] >> 8) & 0xFF
        cls.PACKET[128] = adcs_data[ADCS_IDX.SUN_VEC_Y] & 0xFF
        # Sun vector Z
        cls.PACKET[129] = (adcs_data[ADCS_IDX.SUN_VEC_Z] >> 24) & 0xFF
        cls.PACKET[130] = (adcs_data[ADCS_IDX.SUN_VEC_Z] >> 16) & 0xFF
        cls.PACKET[131] = (adcs_data[ADCS_IDX.SUN_VEC_Z] >> 8) & 0xFF
        cls.PACKET[132] = adcs_data[ADCS_IDX.SUN_VEC_Z] & 0xFF
        # Eclipse bool
        cls.PACKET[133] = adcs_data[ADCS_IDX.ECLIPSE] & 0xFF
        # Light sensor X+
        cls.PACKET[134] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_XP] >> 24) & 0xFF
        cls.PACKET[135] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_XP] >> 16) & 0xFF
        cls.PACKET[136] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_XP] >> 8) & 0xFF
        cls.PACKET[137] = adcs_data[ADCS_IDX.LIGHT_SENSOR_XP] & 0xFF
        # Light sensor X-
        cls.PACKET[138] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_XM] >> 24) & 0xFF
        cls.PACKET[139] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_XM] >> 16) & 0xFF
        cls.PACKET[140] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_XM] >> 8) & 0xFF
        cls.PACKET[141] = adcs_data[ADCS_IDX.LIGHT_SENSOR_XM] & 0xFF
        # Light sensor Y+
        cls.PACKET[142] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_YP] >> 24) & 0xFF
        cls.PACKET[143] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_YP] >> 16) & 0xFF
        cls.PACKET[144] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_YP] >> 8) & 0xFF
        cls.PACKET[145] = adcs_data[ADCS_IDX.LIGHT_SENSOR_YP] & 0xFF
        # Light sensor Y-
        cls.PACKET[146] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_YM] >> 24) & 0xFF
        cls.PACKET[147] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_YM] >> 16) & 0xFF
        cls.PACKET[148] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_YM] >> 8) & 0xFF
        cls.PACKET[149] = adcs_data[ADCS_IDX.LIGHT_SENSOR_YM] & 0xFF
        # Light sensor Z+ 1
        cls.PACKET[150] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_ZP1] >> 24) & 0xFF
        cls.PACKET[151] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_ZP1] >> 16) & 0xFF
        cls.PACKET[152] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_ZP1] >> 8) & 0xFF
        cls.PACKET[153] = adcs_data[ADCS_IDX.LIGHT_SENSOR_ZP1] & 0xFF

        # Light sensor Z+ 2
        cls.PACKET[154] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_ZP2] >> 24) & 0xFF
        cls.PACKET[155] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_ZP2] >> 16) & 0xFF
        cls.PACKET[156] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_ZP2] >> 8) & 0xFF
        cls.PACKET[157] = adcs_data[ADCS_IDX.LIGHT_SENSOR_ZP2] & 0xFF

        # Light sensor Z+ 3
        cls.PACKET[158] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_ZP3] >> 24) & 0xFF
        cls.PACKET[159] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_ZP3] >> 16) & 0xFF
        cls.PACKET[160] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_ZP3] >> 8) & 0xFF
        cls.PACKET[161] = adcs_data[ADCS_IDX.LIGHT_SENSOR_ZP3] & 0xFF

        # Light sensor Z+ 4
        cls.PACKET[162] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_ZP4] >> 24) & 0xFF
        cls.PACKET[163] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_ZP4] >> 16) & 0xFF
        cls.PACKET[164] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_ZP4] >> 8) & 0xFF
        cls.PACKET[165] = adcs_data[ADCS_IDX.LIGHT_SENSOR_ZP4] & 0xFF

        # Light sensor Z-
        cls.PACKET[166] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_ZM] >> 24) & 0xFF
        cls.PACKET[167] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_ZM] >> 16) & 0xFF
        cls.PACKET[168] = (adcs_data[ADCS_IDX.LIGHT_SENSOR_ZM] >> 8) & 0xFF
        cls.PACKET[169] = adcs_data[ADCS_IDX.LIGHT_SENSOR_ZM] & 0xFF

        # XP coil status
        cls.PACKET[170] = adcs_data[ADCS_IDX.XP_COIL_STATUS] & 0xFF
        # XM coil status
        cls.PACKET[171] = adcs_data[ADCS_IDX.XM_COIL_STATUS] & 0xFF
        # YP coil status
        cls.PACKET[172] = adcs_data[ADCS_IDX.YP_COIL_STATUS] & 0xFF
        # YM coil status
        cls.PACKET[173] = adcs_data[ADCS_IDX.YM_COIL_STATUS] & 0xFF
        # ZP coil status
        cls.PACKET[174] = adcs_data[ADCS_IDX.ZP_COIL_STATUS] & 0xFF
        # ZM coil status
        cls.PACKET[175] = adcs_data[ADCS_IDX.ZM_COIL_STATUS] & 0xFF

        # Coarse attitude QW
        cls.PACKET[176] = (adcs_data[ADCS_IDX.COARSE_ATTITUDE_QW] >> 24) & 0xFF
        cls.PACKET[177] = (adcs_data[ADCS_IDX.COARSE_ATTITUDE_QW] >> 16) & 0xFF
        cls.PACKET[178] = (adcs_data[ADCS_IDX.COARSE_ATTITUDE_QW] >> 8) & 0xFF
        cls.PACKET[179] = adcs_data[ADCS_IDX.COARSE_ATTITUDE_QW] & 0xFF

        # Coarse attitude QX
        cls.PACKET[180] = (adcs_data[ADCS_IDX.COARSE_ATTITUDE_QX] >> 24) & 0xFF
        cls.PACKET[181] = (adcs_data[ADCS_IDX.COARSE_ATTITUDE_QX] >> 16) & 0xFF
        cls.PACKET[182] = (adcs_data[ADCS_IDX.COARSE_ATTITUDE_QX] >> 8) & 0xFF
        cls.PACKET[183] = adcs_data[ADCS_IDX.COARSE_ATTITUDE_QX] & 0xFF

        # Coarse attitude QY
        cls.PACKET[184] = (adcs_data[ADCS_IDX.COARSE_ATTITUDE_QY] >> 24) & 0xFF
        cls.PACKET[185] = (adcs_data[ADCS_IDX.COARSE_ATTITUDE_QY] >> 16) & 0xFF
        cls.PACKET[186] = (adcs_data[ADCS_IDX.COARSE_ATTITUDE_QY] >> 8) & 0xFF
        cls.PACKET[187] = adcs_data[ADCS_IDX.COARSE_ATTITUDE_QY] & 0xFF

        # Coarse attitude QZ
        cls.PACKET[188] = (adcs_data[ADCS_IDX.COARSE_ATTITUDE_QZ] >> 24) & 0xFF
        cls.PACKET[189] = (adcs_data[ADCS_IDX.COARSE_ATTITUDE_QZ] >> 16) & 0xFF
        cls.PACKET[190] = (adcs_data[ADCS_IDX.COARSE_ATTITUDE_QZ] >> 8) & 0xFF
        cls.PACKET[191] = adcs_data[ADCS_IDX.COARSE_ATTITUDE_QZ] & 0xFF

        # Star tracker status
        cls.PACKET[192] = adcs_data[ADCS_IDX.STAR_TRACKER_STATUS] & 0xFF

        # Star tracker attitude QW
        cls.PACKET[193] = (adcs_data[ADCS_IDX.STAR_TRACKER_ATTITUDE_QW] >> 24) & 0xFF
        cls.PACKET[194] = (adcs_data[ADCS_IDX.STAR_TRACKER_ATTITUDE_QW] >> 16) & 0xFF
        cls.PACKET[195] = (adcs_data[ADCS_IDX.STAR_TRACKER_ATTITUDE_QW] >> 8) & 0xFF
        cls.PACKET[196] = adcs_data[ADCS_IDX.STAR_TRACKER_ATTITUDE_QW] & 0xFF

        # Star tracker attitude QX
        cls.PACKET[197] = (adcs_data[ADCS_IDX.STAR_TRACKER_ATTITUDE_QX] >> 24) & 0xFF
        cls.PACKET[198] = (adcs_data[ADCS_IDX.STAR_TRACKER_ATTITUDE_QX] >> 16) & 0xFF
        cls.PACKET[199] = (adcs_data[ADCS_IDX.STAR_TRACKER_ATTITUDE_QX] >> 8) & 0xFF
        cls.PACKET[200] = adcs_data[ADCS_IDX.STAR_TRACKER_ATTITUDE_QX] & 0xFF

        # Star tracker attitude QY
        cls.PACKET[201] = (adcs_data[ADCS_IDX.STAR_TRACKER_ATTITUDE_QY] >> 24) & 0xFF
        cls.PACKET[202] = (adcs_data[ADCS_IDX.STAR_TRACKER_ATTITUDE_QY] >> 16) & 0xFF
        cls.PACKET[203] = (adcs_data[ADCS_IDX.STAR_TRACKER_ATTITUDE_QY] >> 8) & 0xFF
        cls.PACKET[204] = adcs_data[ADCS_IDX.STAR_TRACKER_ATTITUDE_QY] & 0xFF

        # Star tracker attitude QZ
        cls.PACKET[205] = (adcs_data[ADCS_IDX.STAR_TRACKER_ATTITUDE_QZ] >> 24) & 0xFF
        cls.PACKET[206] = (adcs_data[ADCS_IDX.STAR_TRACKER_ATTITUDE_QZ] >> 16) & 0xFF
        cls.PACKET[207] = (adcs_data[ADCS_IDX.STAR_TRACKER_ATTITUDE_QZ] >> 8) & 0xFF
        cls.PACKET[208] = adcs_data[ADCS_IDX.STAR_TRACKER_ATTITUDE_QZ] & 0xFF

        ############ GPS fields ############
        # TODO

        ############ Thermal fields ############
        # TODO

        ############ Payload fields ############
        # TODO

        cls.PACKET = bytes(cls.PACKET)
