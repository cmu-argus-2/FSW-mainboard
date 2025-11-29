"""
Payload Message Encoding and Decoding

The serialization and deserialization of messages is hardcoded through class methods
in the Encoder and Decoder classes.

The protocol uses two packet types with fixed sizes:

From the host perspective:
- The ENCODER class will serialize a packet that the communication layer sends through its channel
- The DECODER class will deserialize a packet that the communication layer receives from its channel

The outgoing packet format is as follows:
- Byte 0: Command ID
- Byte 1-31: Command arguments (if any)

ACK/NACK packets (FIXED 6 BYTES):
- Byte 0: Command ID
- Byte 1-2: Sequence count (uint16, big-endian)
- Byte 3-4: Data length = 1 (uint16, big-endian)
- Byte 5: Status byte (ACK or error code)
Total: Always exactly 6 bytes (NO CRC)

Data packets (FIXED 247 BYTES):
- Byte 0: Command ID
- Byte 1-2: Sequence count (uint16, big-endian)
- Byte 3-4: Data length (uint16, big-endian) - indicates actual payload size (≤240)
- Byte 5-244: Data payload (240 bytes, padded with zeros if needed)
- Byte 245-246: CRC16 (uint16, big-endian) covering bytes 0-244
Total: Always exactly 247 bytes


Author: Ibrahima Sory Sow, Perrin Tong

"""
from apps.payload.definitions import (
    ACK,
    CommandID,
    ErrorCodes,
    PayloadErrorCodes,
    PayloadTM,
    Resp_DisableCameras,
    Resp_EnableCameras,
    Resp_RequestNextFilePacket,
    Resp_RequestNextFilePackets,
)
from core import logger

# Asymmetric sizes for send and receive buffers
_RECV_PCKT_BUF_SIZE = 1024  # buffer a bit bigger on purpose
_SEND_PCKT_BUF_SIZE = 32

# Incoming packet structure constants
_CMD_ID_IDX = 0
_SEQ_COUNT_START = 1
_SEQ_COUNT_END = 3
_DATA_LEN_START = 3  # 2-byte data length
_DATA_LEN_END = 5
_DATA_START = 5
_DATA_END = 245  # Always 240 bytes of data (with padding)
_CRC16_START = 245
_CRC16_END = 247
_FIXED_PACKET_SIZE = 247  # All data packets are exactly this size

# CRC16-CCITT parameters
_CRC16_POLY = 0x1021
_CRC16_INIT = 0xFFFF
_CRC16_RESIDUE = 0x0000

# Byte order
_BYTE_ORDER = "big"


def calculate_crc16(data: bytes) -> int:
    """
    Calculate CRC16-CCITT for the given data.

    Args:
        data: Bytes to calculate CRC over

    Returns:
        16-bit CRC value
    """
    crc = _CRC16_INIT

    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ _CRC16_POLY
            else:
                crc = crc << 1
            crc &= 0xFFFF  # Keep it 16-bit

    return crc


def verify_crc16(data_with_crc: bytes) -> bool:
    """
    Verify CRC16 by checking for correct residue.
    When CRC16 is calculated over data+CRC, the result should be the residue value.

    Args:
        data_with_crc: Complete packet including the 2-byte CRC at the end

    Returns:
        True if CRC is valid, False otherwise
    """
    residue = calculate_crc16(data_with_crc)
    return residue == _CRC16_RESIDUE


class Encoder:

    # send buffer
    _send_buffer = bytearray(_SEND_PCKT_BUF_SIZE)

    # Some optimization compatible with CP
    _bytes_set_last_time = 0

    @classmethod
    def clear_buffer(cls):
        # compatible with circuitpython
        for i in range(cls._bytes_set_last_time):
            cls._send_buffer[i] = 0

    @classmethod
    def encode_ping(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.PING_ACK
        cls._bytes_set_last_time = 1
        return cls._send_buffer[:1]

    @classmethod
    def encode_shutdown(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.SHUTDOWN
        cls._bytes_set_last_time = 1
        return cls._send_buffer[:1]

    @classmethod
    def encode_request_telemetry(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.REQUEST_TELEMETRY
        cls._bytes_set_last_time = 1
        return cls._send_buffer[:1]

    @classmethod
    def encode_enable_cameras(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.ENABLE_CAMERAS
        cls._bytes_set_last_time = 1
        return cls._send_buffer[:1]

    @classmethod
    def encode_disable_cameras(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.DISABLE_CAMERAS
        cls._bytes_set_last_time = 1
        return cls._send_buffer[:1]

    @classmethod
    def encode_capture_images(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.CAPTURE_IMAGES
        cls._bytes_set_last_time = 1
        return cls._send_buffer[:1]

    @classmethod
    def encode_start_capture_images_periodically(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.START_CAPTURE_IMAGES_PERIODICALLY
        cls._bytes_set_last_time = 1
        return cls._send_buffer[:1]

    @classmethod
    def encode_stop_capture_images(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.STOP_CAPTURE_IMAGES
        cls._bytes_set_last_time = 1
        return cls._send_buffer[:1]

    @classmethod
    def encode_request_storage_info(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.REQUEST_STORAGE_INFO
        cls._bytes_set_last_time = 1
        return cls._send_buffer[:1]

    @classmethod
    def encode_request_image(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.REQUEST_IMAGE
        cls._bytes_set_last_time = 1
        return cls._send_buffer[:1]

    @classmethod
    def encode_request_next_file_packet(cls, packet_number):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.REQUEST_NEXT_FILE_PACKET
        cls._send_buffer[1:3] = packet_number.to_bytes(2, byteorder=_BYTE_ORDER)
        cls._bytes_set_last_time = 3

        # Debug logging
        from core import logger

        hex_str = " ".join(f"{b:02x}" for b in cls._send_buffer[:3])
        logger.info(f"[DEBUG TX] Encoded REQUEST_NEXT_FILE_PACKET: {hex_str} (packet_nb={packet_number})")

        return cls._send_buffer[:3]  # Only return the bytes we actually set

    @classmethod
    def encode_request_next_file_packets(cls, start_packet, count):
        """
        Encode batch request for multiple packets.
        Format: [cmd_id][start_packet_high][start_packet_low][count]
        """
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.REQUEST_NEXT_FILE_PACKETS
        cls._send_buffer[1:3] = start_packet.to_bytes(2, byteorder=_BYTE_ORDER)
        cls._send_buffer[3] = count
        cls._bytes_set_last_time = 4

        from core import logger

        hex_str = " ".join(f"{b:02x}" for b in cls._send_buffer[:4])
        logger.info(f"[DEBUG TX] Encoded REQUEST_NEXT_FILE_PACKETS: {hex_str} (start={start_packet}, count={count})")

        return cls._send_buffer[:4]

    @classmethod
    def encode_clear_storage(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.CLEAR_STORAGE
        cls._bytes_set_last_time = 1
        return cls._send_buffer[:1]

    @classmethod
    def encode_ping_od_status(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.PING_OD_STATUS
        cls._bytes_set_last_time = 1
        return cls._send_buffer[:1]

    @classmethod
    def encode_run_od(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.RUN_OD
        cls._bytes_set_last_time = 1
        return cls._send_buffer[:1]

    @classmethod
    def encode_request_od_result(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.REQUEST_OD_RESULT
        cls._bytes_set_last_time = 1
        return cls._send_buffer[:1]

    @classmethod
    def encode_synchronize_time(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.SYNCHRONIZE_TIME
        cls._bytes_set_last_time = 1
        return cls._send_buffer[:1]

    @classmethod
    def encode_full_reset(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.FULL_RESET
        cls._bytes_set_last_time = 1
        return cls._send_buffer[:1]

    @classmethod
    def encode_debug_display_camera(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.DEBUG_DISPLAY_CAMERA
        cls._bytes_set_last_time = 1
        return cls._send_buffer[:1]

    @classmethod
    def encode_debug_stop_display(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.DEBUG_STOP_DISPLAY
        cls._bytes_set_last_time = 1
        return cls._send_buffer[:1]

    # Generic example without any checking
    @classmethod
    def encode_with_args(cls, command_id, *args):
        cls.clear_buffer()
        cls._send_buffer[0] = command_id
        for i, arg in enumerate(args, start=1):
            cls._send_buffer[i] = arg
        return cls._send_buffer


class Decoder:

    _recv_buffer = bytearray(_RECV_PCKT_BUF_SIZE)
    _sequence_count_idx = slice(_SEQ_COUNT_START, _SEQ_COUNT_END)
    _data_length_idx = slice(_DATA_LEN_START, _DATA_LEN_END)  # 2-byte data length
    _data_idx = None  # Will be calculated based on actual data length

    _curr_id = 0
    _sequence_count = 0
    _curr_data_length = 0
    _crc_valid = False

    # specific buffer for file packet to be stored there for retrieval
    _file_recv_buffer = bytearray(_RECV_PCKT_BUF_SIZE)

    @classmethod
    def decode(cls, data):
        cls._recv_buffer = data

        # Check packet size: must be either 6 (ACK) or 247 (data packet)
        packet_len = len(data)
        if packet_len == 6:
            # ACK/NACK packet: 5 header + 1 status (NO CRC)
            logger.info("[DEBUG] Received 6-byte ACK packet")
        elif packet_len == _FIXED_PACKET_SIZE:
            # Data packet: 5 header + 240 data + 2 CRC
            logger.info("[DEBUG] Received 247-byte data packet")
        else:
            logger.error(f"[DEBUG] Invalid packet size: {packet_len} (expected 6 or 247)")
            return ErrorCodes.INVALID_PACKET

        # # Debug: print first 20 bytes of packet
        # hex_bytes = ' '.join(f'{b:02x}' for b in data[:min(20, len(data))])
        # logger.info(f"[DEBUG] Received packet (first 20 bytes): {hex_bytes}")

        # header processing
        cls._curr_id = int(cls._recv_buffer[_CMD_ID_IDX])
        cls._sequence_count = int.from_bytes(cls._recv_buffer[_SEQ_COUNT_START:_SEQ_COUNT_END], byteorder=_BYTE_ORDER)
        cls._curr_data_length = int.from_bytes(cls._recv_buffer[_DATA_LEN_START:_DATA_LEN_END], byteorder=_BYTE_ORDER)

        # logger.info(f"[DEBUG] decode(): cmd_id={cls._curr_id}, seq={cls._sequence_count}, data_len={cls._curr_data_length}")

        # Validate based on packet type
        if packet_len == 6:
            # ACK: data_length should be 1, no CRC check
            if cls._curr_data_length != 1:
                logger.error(f"[DEBUG] Invalid ACK data length: {cls._curr_data_length} (expected 1)")
                return ErrorCodes.INVALID_PACKET
            cls._crc_valid = True  # No CRC for ACKs
        else:
            # Data packet: validate data_length and verify CRC
            if cls._curr_data_length > 240:
                logger.error(f"[DEBUG] Invalid data length: {cls._curr_data_length} (max 240)")
                return ErrorCodes.INVALID_PACKET

            # Verify CRC16 over bytes 0-244 (header + data), CRC at bytes 245-246
            # logger.info(f"[DEBUG] CRC bytes at positions 245-246: {data[245]:02x} {data[246]:02x}")

            cls._crc_valid = verify_crc16(cls._recv_buffer)
            if not cls._crc_valid:
                logger.error("[DEBUG] CRC check failed")
                return ErrorCodes.INVALID_PACKET

        # Set data slice for extraction (only extract actual data, not padding)
        cls._data_idx = slice(_DATA_START, _DATA_START + cls._curr_data_length)

        if cls._curr_id == CommandID.PING_ACK:
            return cls.decode_ping()
        elif cls._curr_id == CommandID.SHUTDOWN:
            return cls.decode_shutdown()
        elif cls._curr_id == CommandID.REQUEST_TELEMETRY:
            return cls.decode_request_telemetry()
        elif cls._curr_id == CommandID.ENABLE_CAMERAS:
            return cls.decode_enable_cameras()
        elif cls._curr_id == CommandID.DISABLE_CAMERAS:
            return cls.decode_disable_cameras()
        elif cls._curr_id == CommandID.REQUEST_IMAGE:
            return cls.decode_request_image()
        elif cls._curr_id == CommandID.REQUEST_NEXT_FILE_PACKET:
            return cls.decode_request_next_file()
        elif cls._curr_id == CommandID.REQUEST_NEXT_FILE_PACKETS:
            return cls.decode_request_next_file_packets()
        # rest is coming

    @classmethod
    def current_command_id(cls):
        return cls._curr_id

    @classmethod
    def check_command_id(cls, cmd):
        if cmd not in CommandID.__dict__.values():
            return False
        return True

    @classmethod
    def decode_ping(cls):
        if cls._curr_data_length != 1:
            return ErrorCodes.INVALID_PACKET
        return int(cls._recv_buffer[cls._data_idx][0])

    @classmethod
    def decode_shutdown(cls):
        if cls._curr_data_length == 0:
            return ErrorCodes.INVALID_PACKET

        resp = int(cls._recv_buffer[cls._data_idx][0])

        if resp == ACK.ERROR:
            return ErrorCodes.COMMAND_ERROR_EXECUTION

        if resp == ACK.SUCCESS:
            return ErrorCodes.OK
        else:
            return ErrorCodes.INVALID_RESPONSE

    @classmethod
    def decode_request_telemetry(cls):
        # DO NOT RESET

        if cls._curr_data_length != PayloadTM.DATA_LENGTH_SIZE:
            return ErrorCodes.INVALID_PACKET

        if int(cls._recv_buffer[cls._data_idx][0]) == ACK.ERROR:
            return ErrorCodes.COMMAND_ERROR_EXECUTION

        # Filling the PayloadTM structure

        # System part
        PayloadTM.SYSTEM_TIME = int.from_bytes(cls._recv_buffer[cls._data_idx][0:8], byteorder=_BYTE_ORDER, signed=False)
        PayloadTM.SYSTEM_UPTIME = int.from_bytes(cls._recv_buffer[cls._data_idx][8:12], byteorder=_BYTE_ORDER, signed=False)
        PayloadTM.LAST_EXECUTED_CMD_TIME = int.from_bytes(
            cls._recv_buffer[cls._data_idx][12:16], byteorder=_BYTE_ORDER, signed=False
        )
        PayloadTM.LAST_EXECUTED_CMD_ID = cls._recv_buffer[cls._data_idx][16]
        PayloadTM.PAYLOAD_STATE = cls._recv_buffer[cls._data_idx][17]
        PayloadTM.ACTIVE_CAMERAS = cls._recv_buffer[cls._data_idx][18]
        PayloadTM.CAPTURE_MODE = cls._recv_buffer[cls._data_idx][19]
        PayloadTM.CAM_STATUS[0] = cls._recv_buffer[cls._data_idx][20]
        PayloadTM.CAM_STATUS[1] = cls._recv_buffer[cls._data_idx][21]
        PayloadTM.CAM_STATUS[2] = cls._recv_buffer[cls._data_idx][22]
        PayloadTM.CAM_STATUS[3] = cls._recv_buffer[cls._data_idx][23]
        PayloadTM.IMU_STATUS = cls._recv_buffer[cls._data_idx][24]
        PayloadTM.TASKS_IN_EXECUTION = cls._recv_buffer[cls._data_idx][25]
        PayloadTM.DISK_USAGE = cls._recv_buffer[cls._data_idx][26]
        PayloadTM.LATEST_ERROR = cls._recv_buffer[cls._data_idx][27]
        # Tegrastats part
        PayloadTM.TEGRASTATS_PROCESS_STATUS = bool(cls._recv_buffer[cls._data_idx][28])
        PayloadTM.RAM_USAGE = cls._recv_buffer[cls._data_idx][29]
        PayloadTM.SWAP_USAGE = cls._recv_buffer[cls._data_idx][30]
        PayloadTM.ACTIVE_CORES = cls._recv_buffer[cls._data_idx][31]
        PayloadTM.CPU_LOAD[0] = cls._recv_buffer[cls._data_idx][32]
        PayloadTM.CPU_LOAD[1] = cls._recv_buffer[cls._data_idx][33]
        PayloadTM.CPU_LOAD[2] = cls._recv_buffer[cls._data_idx][34]
        PayloadTM.CPU_LOAD[3] = cls._recv_buffer[cls._data_idx][35]
        PayloadTM.CPU_LOAD[4] = cls._recv_buffer[cls._data_idx][36]
        PayloadTM.CPU_LOAD[5] = cls._recv_buffer[cls._data_idx][37]
        PayloadTM.GPU_FREQ = cls._recv_buffer[cls._data_idx][38]
        PayloadTM.CPU_TEMP = cls._recv_buffer[cls._data_idx][39]
        PayloadTM.GPU_TEMP = cls._recv_buffer[cls._data_idx][40]
        PayloadTM.VDD_IN = int.from_bytes(cls._recv_buffer[cls._data_idx][41:43], byteorder=_BYTE_ORDER, signed=False)
        PayloadTM.VDD_CPU_GPU_CV = int.from_bytes(cls._recv_buffer[cls._data_idx][43:45], byteorder=_BYTE_ORDER, signed=False)
        PayloadTM.VDD_SOC = int.from_bytes(cls._recv_buffer[cls._data_idx][45:47], byteorder=_BYTE_ORDER, signed=False)

        return ErrorCodes.OK

    @classmethod
    def decode_enable_cameras(cls):
        Resp_EnableCameras.reset()

        if cls._curr_data_length <= 1:
            return ErrorCodes.INVALID_PACKET

        if cls._curr_data_length == 5:
            Resp_EnableCameras.num_cam_activated = int(cls._recv_buffer[cls._data_idx][0])
            Resp_EnableCameras.cam_status[0] = int(cls._recv_buffer[cls._data_idx][1])
            Resp_EnableCameras.cam_status[1] = int(cls._recv_buffer[cls._data_idx][2])
            Resp_EnableCameras.cam_status[2] = int(cls._recv_buffer[cls._data_idx][3])
            Resp_EnableCameras.cam_status[3] = int(cls._recv_buffer[cls._data_idx][4])
            return ErrorCodes.OK
        else:
            if int(cls._recv_buffer[cls._data_idx][0]) == ACK.ERROR:
                return int(cls._recv_buffer[cls._data_idx][1])

            return ErrorCodes.INVALID_RESPONSE

    @classmethod
    def decode_disable_cameras(cls):

        Resp_DisableCameras.reset()

        if cls._curr_data_length <= 1:
            return ErrorCodes.INVALID_PACKET

        if cls._curr_data_length == 5:
            Resp_DisableCameras.num_cam_deactivated = int(cls._recv_buffer[cls._data_idx][0])
            Resp_DisableCameras.cam_status[0] = int(cls._recv_buffer[cls._data_idx][1])
            Resp_DisableCameras.cam_status[1] = int(cls._recv_buffer[cls._data_idx][2])
            Resp_DisableCameras.cam_status[2] = int(cls._recv_buffer[cls._data_idx][3])
            Resp_DisableCameras.cam_status[3] = int(cls._recv_buffer[cls._data_idx][4])
            return ErrorCodes.OK
        else:
            if int(cls._recv_buffer[cls._data_idx][0]) == ACK.ERROR:
                return int(cls._recv_buffer[cls._data_idx][1])

            return ErrorCodes.INVALID_RESPONSE

    @classmethod
    def decode_request_image(cls):
        if cls._curr_data_length < 1:
            return ErrorCodes.INVALID_PACKET

        resp = int(cls._recv_buffer[cls._data_idx][0])

        logger.info(
            f"[DEBUG] decode_request_image: data_length={cls._curr_data_length}, resp_byte={resp:#x}, ACK.SUCCESS={ACK.SUCCESS:#x}, ACK.ERROR={ACK.ERROR:#x}"  # noqa: E501
        )

        if resp == ACK.SUCCESS:
            return ErrorCodes.OK
        elif resp == ACK.ERROR:
            if cls._curr_data_length < 2:
                return ErrorCodes.INVALID_PACKET
            err = int(cls._recv_buffer[cls._data_idx][1])
            logger.error(f"[DEBUG] Decoded as ERROR with code: {err}")
            if err == PayloadErrorCodes.FILE_NOT_AVAILABLE:
                return ErrorCodes.FILE_NOT_AVAILABLE
            else:
                return ErrorCodes.INVALID_RESPONSE
        else:
            logger.error(f"[DEBUG] Unknown ACK type: {resp:#x}")
            return ErrorCodes.INVALID_RESPONSE

    @classmethod
    def decode_request_next_file(cls):

        Resp_RequestNextFilePacket.reset()

        if cls._curr_data_length < 1:
            return ErrorCodes.INVALID_PACKET

        # Check if this is an error response
        # Jetson simplified error format: data_len=1, just the error code (no 0x0B prefix)
        first_byte = int(cls._recv_buffer[cls._data_idx][0])

        # If data_len is 1 and first byte looks like an error code (not ACK.SUCCESS=0x0A)
        if cls._curr_data_length == 1:
            if first_byte == ACK.SUCCESS:
                # This shouldn't happen for file packets - success should have data
                logger.warning("[DEBUG] Unexpected SUCCESS ACK for file packet request")
                return ErrorCodes.INVALID_RESPONSE
            else:
                # This is an error code
                Resp_RequestNextFilePacket.error = first_byte
                logger.error(f"[DEBUG] File packet request failed with error code: {first_byte:#x}")

                if Resp_RequestNextFilePacket.error == PayloadErrorCodes.NO_MORE_PACKET_FOR_FILE:
                    Resp_RequestNextFilePacket.no_more_packet_to_receive = True
                    return ErrorCodes.NO_MORE_FILE_PACKET
                elif first_byte == 0x04:  # NO_FILE_READY
                    logger.error("[DEBUG] Jetson reports: NO_FILE_READY - file transfer not initialized")
                    return ErrorCodes.FILE_NOT_AVAILABLE
                else:
                    return ErrorCodes.INVALID_RESPONSE
        else:
            # This is a 242-byte DH packet: [2B length][up to 240B payload][padding]
            # Extract the actual payload using the 2-byte length header from the DH packet
            dh_packet = cls._recv_buffer[cls._data_idx]

            if len(dh_packet) != 242:
                logger.error(f"[DEBUG] Expected 242-byte DH packet, got {len(dh_packet)} bytes")
                return ErrorCodes.INVALID_PACKET

            # Parse 2-byte length header from DH packet (big-endian)
            payload_length = (dh_packet[0] << 8) | dh_packet[1]

            if payload_length > 240:
                logger.error(f"[DEBUG] Invalid DH payload length: {payload_length} (max 240)")
                return ErrorCodes.INVALID_PACKET

            # Extract actual payload (skip 2-byte length header)
            actual_payload = dh_packet[2 : 2 + payload_length]

            Resp_RequestNextFilePacket.received_data_size = len(actual_payload)
            Resp_RequestNextFilePacket.packet_nb = cls._sequence_count
            Resp_RequestNextFilePacket.received_data = actual_payload
            return ErrorCodes.OK

    @classmethod
    def decode_request_next_file_packets(cls):
        """
        Decode batch file packet response.
        This decoder is called once per packet in the batch.
        The controller must call receive() multiple times to get all packets.

        The Jetson extracts payload from DH packets before sending over UART.
        We receive only the payload (≤240 bytes), not the full DH packet.
        """
        # DON'T reset here - reset should happen once before starting batch read
        # Resp_RequestNextFilePackets.reset()  # REMOVED

        if cls._curr_data_length < 1:
            return ErrorCodes.INVALID_PACKET

        # Check if this is an error response
        first_byte = int(cls._recv_buffer[cls._data_idx][0])

        if cls._curr_data_length == 1:
            # Error response - store error
            # DON'T reset if NO_MORE_PACKET - we want to keep packets already received in this batch
            if first_byte != PayloadErrorCodes.NO_MORE_PACKET_FOR_FILE:
                Resp_RequestNextFilePackets.reset()

            Resp_RequestNextFilePackets.error = first_byte
            # NO_MORE_PACKET_FOR_FILE (0x05) is a normal EOF indicator for batch reads; log at INFO
            if first_byte == PayloadErrorCodes.NO_MORE_PACKET_FOR_FILE:
                logger.info(f"[DEBUG] Batch file packet request signaled EOF (code: {first_byte:#x})")
            else:
                logger.error(f"[DEBUG] Batch file packet request failed with error code: {first_byte:#x}")

            if first_byte == 0x04:  # NO_FILE_READY
                return ErrorCodes.FILE_NOT_AVAILABLE
            elif first_byte == PayloadErrorCodes.NO_MORE_PACKET_FOR_FILE:
                return ErrorCodes.NO_MORE_FILE_PACKET
            else:
                return ErrorCodes.INVALID_RESPONSE
        else:
            # Receive payload only (≤240 bytes) - Jetson extracts this from DH packet
            payload = cls._recv_buffer[cls._data_idx]

            if len(payload) > 240:
                logger.error(f"[DEBUG] Payload too large in batch: {len(payload)} bytes (max 240)")
                return ErrorCodes.INVALID_PACKET

            # Store the payload
            Resp_RequestNextFilePackets.packets.append(bytearray(payload))
            Resp_RequestNextFilePackets.count_received = len(Resp_RequestNextFilePackets.packets)

            # Use sequence count to track which packet this is
            if Resp_RequestNextFilePackets.start_packet_nb == 0:
                Resp_RequestNextFilePackets.start_packet_nb = cls._sequence_count

            return ErrorCodes.OK
