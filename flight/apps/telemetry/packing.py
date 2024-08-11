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
    PACKET[1] = 0x01  # sequence count
    PACKET[2] = 252  # packet length

    @classmethod
    def pack_telemetry(cls):

        #### CDH fields
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
        cls.PACKET[8] = cdh_data[CDH_IDX.REBOOT_COUNT] & 0xFF

        # Watchdog Timer
        cls.PACKET[9] = cdh_data[CDH_IDX.WATCHDOG_TIMER] & 0xFF

        # HAL Bitflags
        cls.PACKET[10] = cdh_data[CDH_IDX.HAL_BITFLAGS] & 0xFF

        cls.PACKET = bytes(cls.PACKET)
