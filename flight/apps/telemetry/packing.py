"""

Telemetry packing for transmission

Each fixed-length LoRa Payload is structured as follows
MESSAGE_ID : 1 byte
SEQ_COUNT  : 2 bytes
PACKET_LENGTH: 1 byte
PACKET_DATA  : 252 bytes (for now)


"""
from core.data_handler import DataHandler as DH


class TelemetryPacker:
    """
    Packs telemetry data for transmission
    """

    PACKET = bytearray(256)  # pre-allocated buffer for packing
    PACKET[0] = 0x01  # message ID
    PACKET[1] = 0x01  # sequence count
    PACKET[2] = hex(252)  # packet length

    @classmethod
    def pack_telemetry(cls):

        return cls.PACKET
