"""
Satellite radio class for Argus-1 CubeSat.
Message packing/unpacking for telemetry/file TX
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
    # Hardware abstraction for satellite
    sat = SATELLITE

    # Comms state
    state = COMMS_STATE.TX_HEARTBEAT

    # Init TM frame for preallocating memory
    tm_frame = bytearray(250)

    # Parameters for file downlinking (TEMPORARY HARDCODE)
    filepath = None
    file_ID = 0x00
    file_size = 0
    file_message_count = 0

    # Data for file downlinking
    file_obj = []
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
        Name: get_state
        Description: Get internal COMMS_STATE
    """

    @classmethod
    def get_state(self):
        # Get state
        return self.state

    """
        Name: transition_state
        Description: Update internal COMMS_STATE
    """

    @classmethod
    def transition_state(self, timeout):
        # Check current state
        if self.state == COMMS_STATE.RX:
            # State transitions to TX states only occur from RX state

            # Error handling transition
            if timeout:
                # Lost contact with GS, return to default state
                self.state = COMMS_STATE.TX_HEARTBEAT

            # Transitions based on GS ACKs
            elif self.gs_req_message_ID == MSG_ID.SAT_HEARTBEAT:
                # Send latest TM frame
                self.state = COMMS_STATE.TX_HEARTBEAT

            elif self.gs_req_message_ID == MSG_ID.SAT_FILE_METADATA:
                # Send file metadata
                self.state = COMMS_STATE.TX_METADATA

            elif self.gs_req_message_ID == MSG_ID.SAT_FILE_PKT:
                # Send file packet with specified sequence count
                self.state = COMMS_STATE.TX_FILEPKT

            else:
                # Unknown message ID, return to default state
                self.state = COMMS_STATE.TX_HEARTBEAT

        else:
            # Unconditional branch to RX state
            self.state = COMMS_STATE.RX

    """
        Name: set_tm_frame
        Description: Set internal TM frame for TX
    """

    @classmethod
    def set_tm_frame(self, tm_frame):
        # Set internal TM frame definition
        self.tm_frame = tm_frame

    """
        Name: set_filepath
        Description: Set filepath for comms TX file
    """

    @classmethod
    def set_filepath(self, filepath):
        # Set internal TM frame definition
        self.filepath = filepath

    """
        Name: file_get_metadata
        Description: Get TX file metadata from flash
    """

    @classmethod
    def file_get_metadata(self):
        if not (self.filepath):
            # No file at filepath
            logger.warning("[COMMS ERROR] Undefined TX filepath")

            self.file_ID = 0x00
            self.file_size = 0
            self.file_message_count = 0

        else:
            # Valid filepath from DH, set size and message count
            file_stat = os.stat(self.filepath)
            self.file_ID = 0x01
            self.file_size = int(file_stat[6])
            self.file_message_count = int(self.file_size / FILE_PKTSIZE)

            # Increment 1 to message count to account for division floor
            if (self.file_size % FILE_PKTSIZE) > 0:
                self.file_message_count += 1

            # self.file_obj = open(self.filepath, "rb")

    """
        Name: file_get_packet
        Description: Packetize TX file and store in file array for TX
    """

    @classmethod
    def file_get_packet(self, sq_cnt):
        if self.filepath is not None:
            self.file_obj = open(self.filepath, "rb")

        else:
            logger.warning("[COMMS ERROR] Undefined TX filepath")
            self.file_array = bytes([0x00, 0x00, 0x00, 0x00])

            return 0x00

        # Seek to the correct sq_cnt
        if sq_cnt != self.file_message_count - 1:
            self.file_obj.seek(sq_cnt * FILE_PKTSIZE)
            self.file_array = self.file_obj.read(FILE_PKTSIZE)
            self.file_obj.close()

            return FILE_PKTSIZE

        else:
            last_pkt_size = self.file_size - (self.file_message_count - 1) * FILE_PKTSIZE

            self.file_obj.seek(sq_cnt * FILE_PKTSIZE)
            self.file_array = self.file_obj.read(last_pkt_size)
            self.file_obj.close()

            return last_pkt_size

    """
        Name: file_pack_metadata
        Description: Return file metadata for transmission
    """

    @classmethod
    def file_pack_metadata(self):
        # Generate file metadata and file array
        self.file_get_metadata()

        # Return file metadata payload message
        return self.file_ID.to_bytes(1, "big") + self.file_size.to_bytes(4, "big") + self.file_message_count.to_bytes(2, "big")

    """
        Name: listen
        Description: Switch radio to RX mode
    """

    @classmethod
    def listen(self):
        self.sat.RADIO.listen()

    """
        Name: data_available
        Description: Check if data is available in FIFO buffer
    """

    @classmethod
    def data_available(self):
        return self.sat.RADIO.RX_available()

    """
        Name: receive_message
        Description: Receive and unpack message from GS
    """

    @classmethod
    def receive_message(self):
        # Get packet from radio over SPI
        # Assumes packet is in FIFO buffer

        packet = self.sat.RADIO.read_fifo_buffer()

        if packet is None:
            # FIFO buffer does not contain a packet
            self.gs_req_message_ID = 0x00

            return self.gs_req_message_ID

        # Check CRC error on received packet
        crc_check = self.sat.RADIO.crc_error()

        # Increment internal CRC count
        if crc_check > 0:
            self.crc_count += 1

        # Get RX message RSSI
        self.rx_message_rssi = self.sat.RADIO.rssi(raw=True)

        # Unpack RX message header
        self.rx_message_ID = int.from_bytes(packet[0:1], "big")
        self.rx_message_sequence_count = int.from_bytes(packet[1:3], "big")
        self.rx_message_size = int.from_bytes(packet[3:4], "big")

        if self.rx_message_ID == MSG_ID.GS_ACK:
            # GS acknowledged and sent command
            self.gs_rx_message_ID = int.from_bytes(packet[4:5], "big")
            self.gs_req_message_ID = int.from_bytes(packet[5:6], "big")
            self.gs_req_seq_count = int.from_bytes(packet[6:8], "big")

            # Verify GS RX message ID with previously transmitted message ID
            if self.tx_message_ID != self.gs_rx_message_ID:
                # RX ID mismatch, reset GS RQ'd ID
                logger.warning(f"[COMMS ERROR] GS received {self.gs_rx_message_ID}")
                self.gs_req_message_ID = 0x00

                return self.gs_req_message_ID

            # Verify CRC count was 0 for last received message
            if self.crc_count > 0:
                # CRC error, reset GS RQ'd ID
                logger.warning("[COMMS ERROR] CRC error occured")
                self.gs_req_message_ID = 0x00

                return self.gs_req_message_ID

        else:
            # Unknown message ID, reset GS RQ' ID
            self.gs_req_message_ID = 0x00

        return self.gs_req_message_ID

    """
        Name: transmit_file_metadata
        Description: Generate TX message for file metadata
    """

    @classmethod
    def transmit_file_metadata(self):
        # Transmit stored file info
        tx_header = bytes(
            [
                (MSG_ID.SAT_FILE_METADATA),
                0x0,
                0x0,
                0x7,
            ]
        )

        # Get file metatdata
        tx_payload = self.file_pack_metadata()
        # Pack entire message
        self.tx_message = tx_header + tx_payload

    """
        Name: transmit_file_packet
        Description: Generate TX message for file packet
    """

    @classmethod
    def transmit_file_packet(self):
        # Get bytes from file (stored in file_array)
        pkt_size = self.file_get_packet(self.gs_req_seq_count)

        tx_header = (
            (MSG_ID.SAT_FILE_PKT).to_bytes(1, "big")
            + (self.gs_req_seq_count).to_bytes(2, "big")
            + (pkt_size).to_bytes(1, "big")
        )

        # Pack entire message
        self.tx_message = tx_header + self.file_array

    """
        Name: transmit_message
        Description: Transmit message via the LoRa module
    """

    @classmethod
    def transmit_message(self):
        # Check comms state and TX message accordingly
        if self.state == COMMS_STATE.TX_HEARTBEAT:
            # Transmit SAT heartbeat
            self.tx_message = self.tm_frame

        elif self.state == COMMS_STATE.TX_METADATA:
            # Transmit file metatdata
            self.transmit_file_metadata()

        elif self.state == COMMS_STATE.TX_FILEPKT:
            # Transmit file packets with requested sequence count
            self.transmit_file_packet()

        else:
            # Unknown state, just send
            logger.warning(f"[COMMS ERROR] SAT received {self.gs_rq_message_ID}")
            self.tx_message = self.tm_frame

        # Send a message to GS
        self.sat.RADIO.send(self.tx_message)
        self.crc_count = 0

        # Return TX message header
        self.tx_message_ID = int.from_bytes(self.tx_message[0:1], "big")
        return self.tx_message_ID
