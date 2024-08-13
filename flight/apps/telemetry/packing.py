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
        # TODO

        ############ GPS fields ############
        # TODO

        ############ Thermal fields ############
        # TODO

        ############ Payload fields ############
        # TODO

        cls.PACKET = bytes(cls.PACKET)
