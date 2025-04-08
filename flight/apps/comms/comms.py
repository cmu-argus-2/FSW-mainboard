"""
Satellite radio class for Argus-1 CubeSat.
Message packing/unpacking for telemetry/file TX
and acknowledgement RX.

Authors: Akshat Sahay, Ibrahima S. Sow
"""

import os

from apps.command.constants import file_ids_str
from core import logger
from core.data_handler import extract_time_from_filename
from hal.configuration import SATELLITE
from micropython import const

# File packet size for downlinking
_FILE_PKTSIZE = const(240)

# Internal error definitions from driver
_ERR_NONE = const(0)
_ERR_CRC_MISMATCH = const(-7)


# Internal comms states for statechart
class COMMS_STATE:
    TX_HEARTBEAT = 0x01

    RX = 0x02

    TX_ACK = 0x03

    TX_FRAME = 0x04

    TX_FILEPKT = 0x05
    TX_METADATA = 0x06


# Message ID database for communication protocol
class MSG_ID:
    """
    Comms message IDs that are downlinked during the mission
    """

    """
    Source Header IDs
    -----------------
    These IDs are used in the source header [src, dst]. They are
    used to determine which spacecraft a message originates from
    or is meant for.

    ARGUS_ID is the ID associated with the SC. It must be unique
    for Argus-1 and Argus-2. This is the unique TM identifier
    for each spacecraft. This helps in distinguishing the Sc, and
    is also a requirement for FCC licensing.

    GS_ID is a genericized ID specifying that the packet either
    came from [src] or is going to [dst] a ground station. This
    does not specify a particular GS, only that the packet is
    associated with a downlink / uplink.
    """

    # Header ID for Argus - THIS MUST BE UNIQUE FOR EACH SPACECRAFT
    ARGUS_ID = 0x01

    # Header ID for all ground stations (genericized)
    GS_ID = 0x04

    # SAT heartbeat, nominally downlinked in orbit
    SAT_HEARTBEAT = 0x01

    # SAT TM frames, requested by GS
    SAT_TM_NOMINAL = 0x05
    SAT_TM_HAL = 0x02
    SAT_TM_STORAGE = 0x03
    SAT_TM_PAYLOAD = 0x04

    # SAT ACK, in response to GS commands
    SAT_ACK = 0x0F

    # SAT file metadata and file content messages
    SAT_FILE_METADATA = 0x10
    SAT_FILE_PKT = 0x20

    """
    Comms internal state management uses ranges of GS command IDs
    """

    # GS commands SC responds to with an ACK
    GS_CMD_ACK_L = 0x40
    GS_CMD_ACK_H = 0x45

    # GS commands SC responds to with a frame
    GS_CMD_FRM_L = 0x46
    GS_CMD_FRM_H = 0x49

    # GS commands SC responds to with file MD or packets
    GS_CMD_FILE_METADATA = 0x4A
    GS_CMD_FILE_PKT = 0x4B


class SATELLITE_RADIO:
    # Comms state
    state = COMMS_STATE.TX_HEARTBEAT

    # Init TM frame for preallocating memory
    tm_frame = bytearray(248)

    # Parameters for file downlinking (Message ID temporarily hardcoded)
    filepath = None
    file_ID = 0x01
    file_size = 0
    file_time = 1738351687
    file_message_count = 0

    # Data for file downlinking
    file_obj = []
    file_md = []
    file_array = []

    # Last TX'd message parameters
    tx_message_ID = 0x00
    tx_message = []
    tx_ack = 0x04

    # Source header parameters
    rx_src_id = 0x00
    rx_dst_id = 0x00

    # RX'd ID is the latest GS command
    rx_gs_cmd = 0x00

    # RX'd SQ cnt used for packetized file TX
    rx_sq_cnt = 0
    rq_sq_cnt = 0

    # RX'd len used for argument unpacking
    rx_gs_len = 0

    # RX'd payload contains GS arguments
    rx_payload = bytearray()

    # RX'd RSSI logged for error checking
    rx_message_rssi = 0

    # CRC error count
    crc_count = 0

    """
        Name: get_state
        Description: Get internal COMMS_STATE
    """

    @classmethod
    def get_state(cls):
        # Get state
        return cls.state

    """
        Name: transition_state
        Description: Update internal COMMS_STATE
    """

    @classmethod
    def transition_state(cls, rx_count, rx_threshold):
        # Check current state
        if cls.state == COMMS_STATE.RX:
            # State transitions to TX states only occur from RX state

            if rx_count >= rx_threshold:
                # Lost contact with GS, return to default state
                cls.state = COMMS_STATE.TX_HEARTBEAT

            elif cls.rx_gs_cmd >= MSG_ID.GS_CMD_ACK_L and cls.rx_gs_cmd <= MSG_ID.GS_CMD_ACK_H:
                # GS CMD requires an ACK in response
                cls.state = COMMS_STATE.TX_ACK

            elif cls.rx_gs_cmd >= MSG_ID.GS_CMD_FRM_L and cls.rx_gs_cmd <= MSG_ID.GS_CMD_FRM_H:
                # GS CMD requires a frame in response
                cls.state = COMMS_STATE.TX_FRAME

            elif cls.rx_gs_cmd == MSG_ID.GS_CMD_FILE_METADATA:
                # GS CMD requires file metadata in response
                cls.state = COMMS_STATE.TX_METADATA

            elif cls.rx_gs_cmd == MSG_ID.GS_CMD_FILE_PKT:
                # GS CMD requires a file packet in response
                cls.state = COMMS_STATE.TX_FILEPKT

            elif rx_count < rx_threshold:
                # No timeout yet, stay in RX state
                cls.state = COMMS_STATE.RX

            else:
                # Unknown message ID, return to default state
                cls.state = COMMS_STATE.TX_HEARTBEAT

        else:
            # Unconditional branch to RX state
            cls.state = COMMS_STATE.RX

    """
        Name: get_rssi
        Description: Get RSSI of received packet
    """

    @classmethod
    def get_rssi(cls):
        # Get state
        return cls.rx_message_rssi

    """
        Name: set_tx_ack
        Description: Set internal TX ACK for GS ACKs
    """

    @classmethod
    def set_tx_ack(cls, tx_ack):
        # Set internal TX ACK definition
        cls.tx_ack = tx_ack

    """
        Name: set_tm_frame
        Description: Set internal TM frame for TX
    """

    @classmethod
    def set_tm_frame(cls, tm_frame):
        # Set internal TM frame definition
        cls.tm_frame = tm_frame

    """
        Name: set_rx_gs_cmd
        Description: Set RX message ID
    """

    @classmethod
    def set_rx_gs_cmd(cls, rx_gs_cmd):
        # Set internal filepath
        cls.rx_gs_cmd = rx_gs_cmd

    """
        Name: set_filepath
        Description: Set filepath for comms TX file
    """

    @classmethod
    def set_filepath(cls, filepath):
        # Set internal filepath
        cls.filepath = filepath

    """
        Name: get_rx_payload
        Description: Get most recent RX payload
    """

    @classmethod
    def get_rx_payload(cls):
        # Get most recent RX payload
        return cls.rx_payload

    """
        Name: data_available
        Description: Check if data is available in FIFO buffer
    """

    @classmethod
    def data_available(cls):
        if SATELLITE.RADIO_AVAILABLE:
            return SATELLITE.RADIO.RX_available()
        else:
            logger.error("[COMMS ERROR] RADIO no longer active on SAT")
            return False

    """
        Name: file_get_metadata
        Description: Get TX file metadata from flash
    """

    @classmethod
    def file_get_metadata(cls):
        if not (cls.filepath):
            # No file at filepath
            logger.warning("[COMMS ERROR] Undefined TX filepath")

            cls.file_ID = 0x00
            cls.file_time = 0
            cls.file_size = 0
            cls.file_message_count = 0

        else:
            # Valid filepath from DH, set size and message count
            file_stat = os.stat(cls.filepath)

            # Extract file_tag from filepath
            file_tag = cls.filepath.split("/")[2]
            cls.file_ID = file_ids_str[file_tag]

            # Extract file_time from filepath
            cls.file_time = extract_time_from_filename(cls.filepath)

            cls.file_size = int(file_stat[6])
            cls.file_message_count = int(cls.file_size / _FILE_PKTSIZE)

            # Increment 1 to message count to account for division floor
            if (cls.file_size % _FILE_PKTSIZE) > 0:
                cls.file_message_count += 1

    """
        Name: file_get_packet
        Description: Packetize TX file and store in file array for TX
    """

    @classmethod
    def file_get_packet(cls, sq_cnt):
        if cls.filepath is not None:
            cls.file_obj = open(cls.filepath, "rb")

        else:
            logger.warning("[COMMS ERROR] Undefined TX filepath")
            cls.file_array = bytes([0x00])

            # Return file array size
            return 1

        # Check if the sequence count is valid
        if sq_cnt >= cls.file_message_count:
            logger.warning("[COMMS ERROR] Invalid sequence count")
            cls.file_array = bytes([0x00])

            # Return file array size
            return 1

        # Seek to the correct sq_cnt
        if sq_cnt != cls.file_message_count - 1:
            cls.file_obj.seek(sq_cnt * _FILE_PKTSIZE)
            cls.file_array = cls.file_obj.read(_FILE_PKTSIZE)
            cls.file_obj.close()

            return _FILE_PKTSIZE

        else:
            last_pkt_size = cls.file_size - (cls.file_message_count - 1) * _FILE_PKTSIZE

            cls.file_obj.seek(sq_cnt * _FILE_PKTSIZE)
            cls.file_array = cls.file_obj.read(last_pkt_size)
            cls.file_obj.close()

            return last_pkt_size

    """
        Name: file_pack_metadata
        Description: Return file metadata for transmission
    """

    @classmethod
    def file_pack_metadata(cls):
        # Generate file metadata and file array
        cls.file_get_metadata()

        # Write the file metadata to class array for metadata
        cls.file_md = (
            cls.file_ID.to_bytes(1, "big")
            + cls.file_time.to_bytes(4, "big")
            + cls.file_size.to_bytes(4, "big")
            + cls.file_message_count.to_bytes(2, "big")
        )

    """
        Name: transmit_file_metadata
        Description: Generate TX message for file metadata
    """

    @classmethod
    def transmit_file_metadata(cls):
        # Pack header
        tx_header = bytes(
            [
                (MSG_ID.SAT_FILE_METADATA),
                0x0,
                0x0,
                0xB,
            ]
        )

        # Get file metatdata
        cls.file_pack_metadata()

        # Pack entire message
        cls.tx_message = tx_header + cls.file_md

    """
        Name: transmit_file_packet
        Description: Generate TX message for file packet
    """

    @classmethod
    def transmit_file_packet(cls):
        # Get bytes from file (stored in file_array)
        pkt_size = cls.file_get_packet(cls.rq_sq_cnt)

        # Pack header
        tx_header = (
            (MSG_ID.SAT_FILE_PKT).to_bytes(1, "big") + (cls.rq_sq_cnt).to_bytes(2, "big") + (pkt_size + 5).to_bytes(1, "big")
        )

        # Pack entire message
        cls.tx_message = tx_header + cls.file_ID.to_bytes(1, "big") + cls.file_time.to_bytes(4, "big") + cls.file_array

    """
        Name: check_rq_file_params
        Description: Compare stored file params to
        the requested GS file params
    """

    @classmethod
    def check_rq_file_params(cls, packet):
        """
        If file MD requested, use this to see if
        new filepath is needed, and RQ CDH for one.

        If file PKT requested and params do not match,
        this is used for error detection to default to HB state.

        For now, assume that hardcoded filepath
        matches the file the GS requested
        """

        if not (cls.filepath):
            # File does not match
            logger.warning("[COMMS ERROR] Undefined TX filepath")
            return False
        else:
            # Check if request matches stored filepath
            if cls.file_ID != int.from_bytes(packet[0:1], "big"):
                # File does not match
                bad_id = int.from_bytes(packet[0:1], "big")
                logger.warning(f"[COMMS ERROR] File ID does not match {cls.file_ID}, {bad_id}")
                return False

            # Check if request matches stored file time
            elif cls.file_time != int.from_bytes(packet[1:5], "big"):
                # File does not match
                bad_time = int.from_bytes(packet[1:5], "big")
                logger.warning(f"[COMMS ERROR] File time does not match {cls.file_time}, {bad_time}")
                return False

            else:
                # File matches
                return True

    """
        Name: receive_message
        Description: Receive and unpack message from GS
    """

    @classmethod
    def receive_message(cls):
        # Get packet from radio over SPI
        # Assumes packet is in FIFO buffer

        if SATELLITE.RADIO_AVAILABLE:
            packet, err = SATELLITE.RADIO.recv(len=0, timeout_en=True, timeout_ms=1000)
        else:
            logger.error("[COMMS ERROR] RADIO no longer active on SAT")

        # Checks on err returned by driver
        if err == _ERR_CRC_MISMATCH:
            # CRC error, packet likely corrupted
            logger.warning("[COMMS ERROR] CRC error occured on incoming packet")
            cls.rx_gs_cmd = 0x00
            cls.rx_sq_cnt = 0
            cls.rx_gs_len = 0
            return cls.rx_gs_cmd

        elif err != _ERR_NONE:
            # Undefined error, packet should never have gotten to comms task
            logger.error("[COMMS ERROR] Undefined error from radio driver")
            cls.rx_gs_cmd = 0x00
            cls.rx_sq_cnt = 0
            cls.rx_gs_len = 0
            return cls.rx_gs_cmd

        # Check if packet exists
        if packet is None:
            # FIFO buffer does not contain a packet
            cls.rx_gs_cmd = 0x00
            cls.rx_sq_cnt = 0
            cls.rx_gs_len = 0
            return cls.rx_gs_cmd

        # Check packet integrity based on header length
        if len(packet) < 6:
            # Packet does not contain valid Argus header
            logger.warning("[COMMS ERROR] RX'd packet has invalid header")
            cls.rx_gs_cmd = 0x00
            cls.rx_sq_cnt = 0
            cls.rx_gs_len = 0
            return cls.rx_gs_cmd

        if SATELLITE.RADIO_AVAILABLE:
            cls.rx_message_rssi = SATELLITE.RADIO.rssi()
        else:
            logger.error("[COMMS ERROR] RADIO no longer active on SAT")

        # Unpack source header
        cls.rx_src_id = int.from_bytes(packet[0:1], "big")
        cls.rx_dst_id = int.from_bytes(packet[1:2], "big")
        packet = packet[2:]

        # Check packet integrity based on rx_src_id
        if cls.rx_src_id != MSG_ID.GS_ID:
            # Packet does not contain valid CMD_ID
            logger.warning("[COMMS ERROR] RX'd packet has invalid source")
            cls.rx_gs_cmd = 0x00
            cls.rx_sq_cnt = 0
            cls.rx_gs_len = 0
            return cls.rx_gs_cmd

        # Check packet integrity based on rx_dst_id
        if cls.rx_dst_id != MSG_ID.ARGUS_ID:
            # Packet does not contain valid CMD_ID
            logger.warning("[COMMS ERROR] RX'd packet has invalid destination")
            cls.rx_gs_cmd = 0x00
            cls.rx_sq_cnt = 0
            cls.rx_gs_len = 0
            return cls.rx_gs_cmd

        # Unpack RX message header
        cls.rx_gs_cmd = int.from_bytes(packet[0:1], "big")
        cls.rx_sq_cnt = int.from_bytes(packet[1:3], "big")
        cls.rx_gs_len = int.from_bytes(packet[3:4], "big")

        # Check packet integrity based on CMD_ID
        if (cls.rx_gs_cmd < MSG_ID.GS_CMD_ACK_L) or (cls.rx_gs_cmd > MSG_ID.GS_CMD_FILE_PKT):
            # Packet does not contain valid CMD_ID
            logger.warning("[COMMS ERROR] RX'd packet has invalid CMD")
            cls.rx_gs_cmd = 0x00
            cls.rx_sq_cnt = 0
            cls.rx_gs_len = 0
            return cls.rx_gs_cmd

        # Check packet integrity based on message length
        if (len(packet) - 4) != cls.rx_gs_len:
            # Header length does not match packet length
            logger.warning("[COMMS ERROR] RX'd packet has length mismatch with header")
            cls.rx_gs_cmd = 0x00
            cls.rx_sq_cnt = 0
            cls.rx_gs_len = 0
            return cls.rx_gs_cmd

        # Payload will be everything in message after header, can be empty
        if cls.rx_gs_len != 0:
            cls.rx_payload = packet[4:]
        else:
            cls.rx_payload = bytearray()

        if cls.rx_gs_cmd == MSG_ID.GS_CMD_FILE_PKT:
            if cls.check_rq_file_params(packet[4:]) is False:
                # Filepath does not match

                # Error, send down empty file array to signal the error
                logger.warning("[COMMS ERROR] Filepath requested from the GS does not exist")
                cls.filepath = None
                cls.rq_sq_cnt = 0

            else:
                # Filepath matches, move forward with request

                # Get sq_cnt for the PKT
                cls.rq_sq_cnt = int.from_bytes(packet[9:11], "big")

        else:
            # Not a file request, do nothing
            pass

        return cls.rx_gs_cmd

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

        elif cls.state == COMMS_STATE.TX_ACK:
            # Transmit SAT ACK
            cls.tx_message = bytes([MSG_ID.SAT_ACK, 0x00, 0x00, 0x01, cls.tx_ack])

        elif cls.state == COMMS_STATE.TX_FRAME:
            # Transmit a specific TM frame
            cls.tx_message = cls.tm_frame

        elif cls.state == COMMS_STATE.TX_METADATA:
            # Transmit file metatdata
            cls.transmit_file_metadata()

        elif cls.state == COMMS_STATE.TX_FILEPKT:
            # Transmit file packets with requested sequence count
            cls.transmit_file_packet()

        else:
            # Unknown state, just send
            logger.warning(f"[COMMS ERROR] SAT received {cls.gs_rq_message_ID}")
            cls.tx_message = cls.tm_frame

        # Add source header (source and destination) to distinguish between spacecraft
        cls.tx_message = bytes([MSG_ID.ARGUS_ID, MSG_ID.GS_ID]) + cls.tx_message

        # Send a message to GS
        if SATELLITE.RADIO_AVAILABLE:
            SATELLITE.RADIO.send(cls.tx_message)
            cls.crc_count = 0
        else:
            logger.error("[COMMS ERROR] RADIO no longer active on SAT")

        # Return TX message header
        cls.tx_message_ID = int.from_bytes(cls.tx_message[2:3], "big")
        return cls.tx_message_ID
