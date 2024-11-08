"""
Satellite radio class for Argus-1 CubeSat.
Message packing/unpacking for telemetry/image TX
and acknowledgement RX.

Authors: Akshat Sahay, Ibrahima S. Sow

By default, the RF module is in RX mode, and returns to it after TX.
"""

import os

from core import logger
from hal.configuration import SATELLITE

FILE_PKTSIZE = 240


class COMMS_STATE:
    TX_HEARTBEAT = 0x00

    RX = 0x01

    TX_METADATA = 0x02
    TX_FILEPKT = 0x03


class MSG_ID:
    SAT_HEARTBEAT = 0x01

    GS_ACK = 0x08
    SAT_ACK = 0x09

    SAT_FILE_METADATA = 0x10

    SAT_FILE_PKT = 0x20


class SATELLITE_RADIO:

    # Comms state
    state = COMMS_STATE.TX_HEARTBEAT

    # Init TM frame for preallocating memory
    tm_frame = bytearray(250)

    # Parameters for file downlinking
    filepath = ""
    file_ID = 0x00
    file_size = 0
    file_message_count = 0

    # Data for file downlinking
    file_array = []

    # Last TX'd message ID
    tx_message_ID = 0x00
    tx_message = []

    # Last RX'd message parameters
    rx_message_ID = 0x00
    rx_message_sequence_count = 0
    rx_message_size = 0
    rx_message_rssi = 0

    # Payload for GS ACKs, used for comms state and error checking
    gs_rx_message_ID = 0x0
    gs_req_message_ID = 0x0
    gs_req_seq_count = 0

    # CRC error count
    crc_count = 0

    """
        Name: file_get_metadata
        Description: Get TX file metadata from flash
    """

    @classmethod
    def file_get_metadata(cls):
        if not (cls.filepath):
            # No file at filepath
            cls.file_ID = 0x00
            cls.file_size = 0
            cls.file_message_count = 0

        else:
            # Valid filepath from DH, set size and message count
            file_stat = os.stat(cls.filepath)
            cls.file_size = int(file_stat[6])
            cls.file_message_count = int(cls.file_size / FILE_PKTSIZE)

            if (cls.file_size % FILE_PKTSIZE) > 0:
                cls.file_message_count += 1

            cls.file_packetize()

    """
        Name: file_packetize
        Description: Packetize TX file and store in file array for TX
    """

    @classmethod
    def file_packetize(cls):
        # Initialize / empty file array
        cls.file_array = []

        # Get file data
        bytes_remaining = cls.file_size
        send_bytes = open(cls.filepath, "rb")

        # Loop through file and store contents in an array
        while bytes_remaining > 0:
            if bytes_remaining >= FILE_PKTSIZE:
                cls.file_array.append(send_bytes.read(FILE_PKTSIZE))
            else:
                cls.file_array.append(send_bytes.read(bytes_remaining))

            bytes_remaining -= FILE_PKTSIZE

        # Close file when complete
        send_bytes.close()

    """
        Name: file_pack_metadata
        Description: Return file metadata for transmission
    """

    @classmethod
    def file_pack_metadata(cls):
        return cls.file_ID.to_bytes(1, "big") + cls.file_size.to_bytes(4, "big") + cls.file_message_count.to_bytes(2, "big")

    """
        Name: listen
        Description: Switch radio to RX mode
    """

    @classmethod
    def listen(cls):
        SATELLITE.RADIO.listen()

    """
        Name: idle
        Description: Switch radio to idle mode

    """

    @classmethod
    def idle(cls):
        SATELLITE.RADIO.idle()

    """
        Name: data_available
        Description: Check if data is available in FIFO buffer

    """

    @classmethod
    def data_available(cls):
        return SATELLITE.RADIO.RX_available()

    """
        Name: receive_message
        Description: Receive and unpack message from GS

    """

    @classmethod
    def receive_message(cls):
        # Get packet from radio over SPI
        # Assumes packet is in FIFO buffer

        packet = SATELLITE.RADIO.read_fifo_buffer()

        if packet is None:
            # FIFO buffer does not contain a packet
            cls.state = COMMS_STATE.TX_HEARTBEAT
            cls.gs_req_message_ID = 0x00

            return cls.gs_req_message_ID

        # Check CRC error on received packet
        crc_check = SATELLITE.RADIO.crc_error()

        # Increment internal CRC count
        if crc_check > 0:
            cls.crc_count += 1

        # Get RX message RSSI
        cls.rx_message_rssi = SATELLITE.RADIO.rssi(raw=True)

        # Unpack RX message header
        cls.rx_message_ID = int.from_bytes(packet[0:1], "big")
        cls.rx_message_sequence_count = int.from_bytes(packet[1:3], "big")
        cls.rx_message_size = int.from_bytes(packet[3:4], "big")

        if cls.rx_message_ID == MSG_ID.GS_ACK:
            # GS acknowledged and sent command
            cls.gs_rx_message_ID = int.from_bytes(packet[4:5], "big")
            cls.gs_req_message_ID = int.from_bytes(packet[5:6], "big")
            cls.gs_req_seq_count = int.from_bytes(packet[6:8], "big")

            # Verify GS RX message ID with previously transmitted message ID
            if cls.tx_message_ID != cls.gs_rx_message_ID:
                # Logger warning
                logger.warning(f"[COMMS ERROR] GS received {cls.gs_rx_message_ID}")
                cls.state = COMMS_STATE.TX_HEARTBEAT

                return cls.gs_req_message_ID

            # Verify CRC count was 0 for last received message
            if cls.crc_count > 0:
                # Logger warning
                logger.warning("[COMMS ERROR] CRC error occured")
                cls.state = COMMS_STATE.TX_HEARTBEAT

                return cls.gs_req_message_ID

            if cls.gs_req_message_ID == MSG_ID.SAT_HEARTBEAT:
                # Send latest TM frame
                cls.state = COMMS_STATE.TX_HEARTBEAT

            elif cls.gs_req_message_ID == MSG_ID.SAT_FILE_METADATA:
                # Send file metadata
                cls.state = COMMS_STATE.TX_METADATA

            elif cls.gs_req_message_ID == MSG_ID.SAT_FILE_PKT:
                # Send file packet with specified sequence count
                cls.state = COMMS_STATE.TX_FILEPKT

            else:
                # Unknown message ID, return to default state
                cls.state = COMMS_STATE.TX_HEARTBEAT

        else:
            # Unknown message ID, return to default state
            cls.state = COMMS_STATE.TX_HEARTBEAT

        return cls.gs_req_message_ID

    """
        Name: transmit_file_metadata
        Description: Generate TX message for file metadata
    """

    @classmethod
    def transmit_file_metadata(cls):
        # Transmit stored image info
        tx_header = bytes(
            [
                (MSG_ID.SAT_FILE_METADATA),
                0x0,
                0x0,
                0x7,
            ]
        )
        tx_payload = cls.file_pack_metadata()
        cls.tx_message = tx_header + tx_payload

    """
        Name: transmit_file_pkt
        Description: Generate TX message for file packet
    """

    @classmethod
    def transmit_file_pkt(cls):
        tx_header = (
            (MSG_ID.SAT_FILE_PKT).to_bytes(1, "big")
            + (cls.gs_req_seq_count).to_bytes(2, "big")
            + len(cls.file_array[cls.gs_req_seq_count]).to_bytes(1, "big")
        )

        # Payload
        tx_payload = cls.image_array[cls.gs_req_seq_count]
        # Pack entire message
        cls.tx_message = tx_header + tx_payload

    """
        Name: transmit_message
        Description: Transmit message via the LoRa module
    """

    @classmethod
    def transmit_message(cls):
        # Check comms state and TX message accordingly
        if cls.state == COMMS_STATE.TX_HEARTBEAT:
            # Transmit SAT heartbeat
            cls.tx_message = cls.tm_frame

        elif cls.state == COMMS_STATE.TX_METADATA:
            # Transmit file metatdata
            cls.transmit_file_metadata()

        elif cls.state == COMMS_STATE.TX_FILEPKT:
            # Transmit file packets with requested sequence count
            cls.transmit_file_pkt()

        else:
            # Transmit SAT heartbeat
            cls.state = COMMS_STATE.TX_HEARTBEAT
            cls.tx_message = cls.tm_frame

        # Send a message to GS
        SATELLITE.RADIO.send(cls.tx_message)
        cls.crc_count = 0
        cls.state = COMMS_STATE.RX

        # Return TX message header
        cls.tx_message_ID = int.from_bytes(cls.tx_message[0:1], "big")
        return cls.tx_message_ID
