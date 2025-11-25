"""
Satellite radio class for Argus-1 CubeSat.
Message packing/unpacking for telemetry/file TX
and acknowledgement RX.

Authors: Akshat Sahay, Ibrahima S. Sow, Perrin Tong
"""

import os

from apps.command.constants import file_ids_str
from core import logger
from core.data_handler import DataHandler as DH
from core.data_handler import extract_time_from_filename
from hal.configuration import SATELLITE
from micropython import const

# File packet size for downlinking
_FILE_PKTSIZE = const(240)

# Additional file size in file MD/PKT requests for file ID and time
_FILE_ID_TIME_SIZE = const(5)

# Internal error definitions from driver
_ERR_NONE = const(0)
_ERR_CRC_MISMATCH = const(-7)

# Byte order
_BYTE_ORDER = "big"


# Internal comms states for statechart
class COMMS_STATE:
    TX_HEARTBEAT = 0x01

    RX = 0x02

    TX_ACK = 0x03

    TX_FRAME = 0x04

    TX_FILEPKT = 0x05
    TX_METADATA = 0x06

    TX_DOWNLINK_ALL = 0x07


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
    SAT_DOWNLINK_ALL = 0x24

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

    # GS command for downlinking all packets for a file, no protocol
    GS_CMD_DOWNLINK_ALL = 0x50


class SATELLITE_RADIO:
    # Comms state
    state = COMMS_STATE.TX_HEARTBEAT

    # Init TM frame for preallocating memory
    tm_frame = bytearray(248)

    # Parameters for file downlinking
    filepath = None
    file_ID = 0x00
    file_size = 0
    file_time = 0
    file_message_count = 0

    """
    NOTE: This flag can be set to force comms into DOWLINK_ALL.

    Whenever done, ensure that filepath for the desired file is also
    set. When GS_CMD_DOWNLINK_ALL is received, the command contains
    file_ID and file_time, which are used for getting the filepath
    from the DH.
    """
    # Downlink all flag
    dlink_all = False

    # File setup flag for downlink all
    # Only set after the commanding response comes in
    dlink_init = False

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

    # RX SQ cnt, currently unused but in packet structure
    # Can potentially be used for file uplinking....
    rx_sq_cnt = 0

    # RQ'd SQ cnt used for packetized file downlinking
    rq_sq_cnt = 0

    # Internal SQ cnt for a file, used in DOWNLINK_ALL
    int_sq_cnt = 0

    # RX'd packet parameters
    rx_gs_len = 0
    rx_payload = bytearray()
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
        # Check flag and stay in TX_DOWNLINK_ALL if file TX not done
        if cls.dlink_all is True:
            cls.state = COMMS_STATE.TX_DOWNLINK_ALL

        # Check current state
        elif cls.state == COMMS_STATE.RX:
            # State transitions to TX states only occur from RX state
            # Only exception to this is TX_DOWNLINK_ALL

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
        Name: get_downlink_init_flag
        Description: Get downlink init flag

        Flag is set after DOWNLINK_ALL response
        from command processor (gives filepath)
    """

    @classmethod
    def get_downlink_init_flag(cls):
        # Get dlink_init flag
        return cls.dlink_init

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

            # Extract file_tag from filename (format: tag_timestamp.ext)
            # This is more robust than path indices and works with any directory structure
            filename = os.path.basename(cls.filepath)
            file_tag = filename.split("_")[0]
            cls.file_ID = file_ids_str[file_tag]

            # Extract file_time from filepath
            cls.file_time = extract_time_from_filename(cls.filepath)

            cls.file_size = int(file_stat[6])

            # Check if this is a FileProcess (packet-based file)
            if DH.is_file_process(file_tag):
                # For FileProcess, get actual packet count from file
                file_process = DH.data_process_registry.get(file_tag)
                if file_process:
                    cls.file_message_count = file_process.get_packet_count(cls.filepath)
                else:
                    logger.warning(f"[COMMS ERROR] FileProcess {file_tag} not found")
                    cls.file_message_count = 0
            else:
                # For regular DataProcess files, divide by packet size
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
        if cls.filepath is None:
            logger.warning("[COMMS ERROR] Undefined TX filepath")
            cls.file_array = bytes([0x00])
            return 1

        # Check if the sequence count is valid
        if sq_cnt >= cls.file_message_count:
            logger.warning("[COMMS ERROR] Invalid sequence count")
            cls.file_array = bytes([0x00])
            return 1

        # Extract file_tag from filename (format: tag_timestamp.ext)
        # This is more robust than path indices and works with any directory structure
        filename = os.path.basename(cls.filepath)
        file_tag = filename.split("_")[0]

        # Check if this is a FileProcess (packet-based file)
        if DH.is_file_process(file_tag):
            # Use FileProcess packet extraction
            file_process = DH.data_process_registry.get(file_tag)
            if file_process:
                result = file_process.get_packet(cls.filepath, sq_cnt)
                if result is not None:
                    length, data = result
                    cls.file_array = bytes(data)
                    return length
                else:
                    logger.warning(f"[COMMS ERROR] Failed to extract packet {sq_cnt}")
                    cls.file_array = bytes([0x00])
                    return 1
            else:
                logger.warning(f"[COMMS ERROR] FileProcess {file_tag} not found")
                cls.file_array = bytes([0x00])
                return 1
        else:
            # For regular DataProcess files, use byte-offset method
            try:
                cls.file_obj = open(cls.filepath, "rb")

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
            except Exception as e:
                logger.error(f"[COMMS ERROR] Failed to read file: {e}")
                cls.file_array = bytes([0x00])
                return 1

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
            cls.file_ID.to_bytes(1, _BYTE_ORDER)
            + cls.file_time.to_bytes(4, _BYTE_ORDER)
            + cls.file_size.to_bytes(4, _BYTE_ORDER)
            + cls.file_message_count.to_bytes(2, _BYTE_ORDER)
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

        # pkt_size + _FILE_ID_TIME_SIZE is to accomodate 5 bytes of file info
        # (file_ID, 1 byte; file_time, 4 bytes) w/ pkt_size bytes of file data
        tx_header = (
            (MSG_ID.SAT_FILE_PKT).to_bytes(1, _BYTE_ORDER)
            + (cls.rq_sq_cnt).to_bytes(2, _BYTE_ORDER)
            + (pkt_size + _FILE_ID_TIME_SIZE).to_bytes(1, _BYTE_ORDER)
        )

        # Pack entire message, file_array contains file info
        cls.tx_message = (
            tx_header + cls.file_ID.to_bytes(1, _BYTE_ORDER) + cls.file_time.to_bytes(4, _BYTE_ORDER) + cls.file_array
        )

    """
        Name: transmit_downlink_all
        Description: Packet downlinking for a file
        that is decoupled from GS commands for each
        packet request

        This will force Argus to stay in TX mode for
        a certain period (depending on file size)
    """

    @classmethod
    def transmit_downlink_all(cls):
        # Run transmit_file_packet with int_sq_cnt

        # Get bytes from file (stored in file_array)
        pkt_size = cls.file_get_packet(cls.int_sq_cnt)

        # Pack header

        # pkt_size + _FILE_ID_TIME_SIZE is to accomodate 5 bytes of file info
        # (file_ID, 1 byte; file_time, 4 bytes) w/ pkt_size bytes of file data
        tx_header = (
            (MSG_ID.SAT_DOWNLINK_ALL).to_bytes(1, _BYTE_ORDER)
            + (cls.int_sq_cnt).to_bytes(2, _BYTE_ORDER)
            + (pkt_size + _FILE_ID_TIME_SIZE).to_bytes(1, _BYTE_ORDER)
        )

        # Pack entire message, file_array contains file info
        cls.tx_message = (
            tx_header + cls.file_ID.to_bytes(1, _BYTE_ORDER) + cls.file_time.to_bytes(4, _BYTE_ORDER) + cls.file_array
        )

        # Check for last packet
        if cls.int_sq_cnt == cls.file_message_count - 1:
            # File downlink is over, set flag to not go back into TX_DOWNLINK_ALL state
            logger.info(f"Finished downlinking file at packet {cls.int_sq_cnt}")
            cls.dlink_all = False
            cls.dlink_init = False

        # Increment internal sequence count
        cls.int_sq_cnt += 1

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
            if cls.file_ID != int.from_bytes(packet[0:1], _BYTE_ORDER):
                # File does not match
                bad_id = int.from_bytes(packet[0:1], _BYTE_ORDER)
                logger.warning(f"[COMMS ERROR] File ID does not match {cls.file_ID}, {bad_id}")
                return False

            # Check if request matches stored file time
            elif cls.file_time != int.from_bytes(packet[1:5], _BYTE_ORDER):
                # File does not match
                bad_time = int.from_bytes(packet[1:5], _BYTE_ORDER)
                logger.warning(f"[COMMS ERROR] File time does not match {cls.file_time}, {bad_time}")
                return False

            else:
                # File matches
                return True

    """
        Name: handle_downlink_all_rq
        Description: On CMD, start request for DOWNLINK_ALL
    """

    @classmethod
    def handle_downlink_all_rq(cls):
        # Command processor returns a filepath in response to DOWNLINK_ALL

        # If valid filepath, set downlink all flag to True for state machine
        if not (cls.filepath):
            # File does not match
            logger.warning("[COMMS ERROR] Undefined TX filepath")
            cls.dlink_all = False
            cls.dlink_init = False

        else:
            # Generate internal metadata for this filepath
            cls.file_get_metadata()
            cls.dlink_all = True
            cls.dlink_init = True
            cls.int_sq_cnt = 0

            logger.info(f"Starting downlink of file for {cls.file_message_count} packets")

    """
        Name: receive_message
        Description: Receive and unpack message from GS
    """

    @classmethod
    def receive_message(cls):
        # Get packet from radio over SPI
        # Assumes packet is in FIFO buffer

        packet = None
        err = -1  # _ERR_NONE is 0

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
        cls.rx_src_id = int.from_bytes(packet[0:1], _BYTE_ORDER)
        cls.rx_dst_id = int.from_bytes(packet[1:2], _BYTE_ORDER)
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
        cls.rx_gs_cmd = int.from_bytes(packet[0:1], _BYTE_ORDER)
        cls.rx_sq_cnt = int.from_bytes(packet[1:3], _BYTE_ORDER)
        cls.rx_gs_len = int.from_bytes(packet[3:4], _BYTE_ORDER)

        # Check packet integrity based on CMD_ID
        if (cls.rx_gs_cmd < MSG_ID.GS_CMD_ACK_L) or (cls.rx_gs_cmd > MSG_ID.GS_CMD_DOWNLINK_ALL):
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

        # GS_CMD_FILE_PKT is handled internally in the comms task
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
                cls.rq_sq_cnt = int.from_bytes(packet[9:11], _BYTE_ORDER)

        # GS_CMD_DOWNLINK_ALL is also handled internally in the comms task
        elif cls.rx_gs_cmd == MSG_ID.GS_CMD_DOWNLINK_ALL:
            # Flag for state transition
            cls.dlink_all = True

            # Flag to indicate a wait time for commanding responses
            cls.dlink_init = False

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

        elif cls.state == COMMS_STATE.TX_DOWNLINK_ALL:
            # Transmit file packets with the internal sequence count
            cls.transmit_downlink_all()

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
        cls.tx_message_ID = int.from_bytes(cls.tx_message[2:3], _BYTE_ORDER)
        return cls.tx_message_ID
