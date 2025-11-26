"""
Payload Message Encoding and Decoding

The serialization and deserialization of messages is hardcoded through class methods
in the Encoder and Decoder classes.

The protocol is straightforward and uses a simple fixed-length message format.

From the host perspective:
- The ENCODER class will serialize a packet that the communication layer sends through its channel
- The DECODER class will deserialize a packet that the communication layer receives from its channel

The outgoing packet format is as follows:
- Byte 0: Command ID
- Byte 1-31: Command arguments (if any)

The incoming packet format is as follows:
- Byte 0: Command ID
- Byte 1-2: Sequence count (uint16, big-endian)
- Byte 3: Data length (uint8)
- Byte 4-243: Data payload (240 bytes max)
- Byte 244-245: CRC16 (uint16, big-endian)
Total: 246 bytes per packet


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
)

# Asymmetric sizes for send and receive buffers
_RECV_PCKT_BUF_SIZE = 256  # buffer a bit bigger on purpose
_SEND_PCKT_BUF_SIZE = 32

# Incoming packet structure constants
_CMD_ID_IDX = 0
_SEQ_COUNT_START = 1
_SEQ_COUNT_END = 3
_DATA_LEN_IDX = 3
_DATA_START = 4
_DATA_END = 244  # 4 + 240 bytes
_CRC16_START = 244
_CRC16_END = 246
_TOTAL_PACKET_SIZE = 246

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
        return cls._send_buffer

    @classmethod
    def encode_shutdown(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.SHUTDOWN
        cls._bytes_set_last_time = 1
        return cls._send_buffer

    @classmethod
    def encode_request_telemetry(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.REQUEST_TELEMETRY
        cls._bytes_set_last_time = 1
        return cls._send_buffer

    @classmethod
    def encode_enable_cameras(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.ENABLE_CAMERAS
        cls._bytes_set_last_time = 1
        return cls._send_buffer

    @classmethod
    def encode_disable_cameras(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.DISABLE_CAMERAS
        cls._bytes_set_last_time = 1
        return cls._send_buffer

    @classmethod
    def encode_capture_images(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.CAPTURE_IMAGES
        cls._bytes_set_last_time = 1
        return cls._send_buffer

    @classmethod
    def encode_start_capture_images_periodically(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.START_CAPTURE_IMAGES_PERIODICALLY
        cls._bytes_set_last_time = 1
        return cls._send_buffer

    @classmethod
    def encode_stop_capture_images(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.STOP_CAPTURE_IMAGES
        cls._bytes_set_last_time = 1
        return cls._send_buffer

    @classmethod
    def encode_request_storage_info(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.REQUEST_STORAGE_INFO
        cls._bytes_set_last_time = 1
        return cls._send_buffer

    @classmethod
    def encode_request_image(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.REQUEST_IMAGE
        cls._bytes_set_last_time = 1
        return cls._send_buffer

    @classmethod
    def encode_request_next_file_packet(cls, packet_number):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.REQUEST_NEXT_FILE_PACKET
        cls._send_buffer[1:3] = packet_number.to_bytes(2, byteorder=_BYTE_ORDER)
        cls._bytes_set_last_time = 3
        return cls._send_buffer

    @classmethod
    def encode_clear_storage(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.CLEAR_STORAGE
        cls._bytes_set_last_time = 1
        return cls._send_buffer

    @classmethod
    def encode_ping_od_status(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.PING_OD_STATUS
        cls._bytes_set_last_time = 1
        return cls._send_buffer

    @classmethod
    def encode_run_od(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.RUN_OD
        cls._bytes_set_last_time = 1
        return cls._send_buffer

    @classmethod
    def encode_request_od_result(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.REQUEST_OD_RESULT
        cls._bytes_set_last_time = 1
        return cls._send_buffer

    @classmethod
    def encode_synchronize_time(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.SYNCHRONIZE_TIME
        cls._bytes_set_last_time = 1
        return cls._send_buffer

    @classmethod
    def encode_full_reset(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.FULL_RESET
        cls._bytes_set_last_time = 1
        return cls._send_buffer

    @classmethod
    def encode_debug_display_camera(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.DEBUG_DISPLAY_CAMERA
        cls._bytes_set_last_time = 1
        return cls._send_buffer

    @classmethod
    def encode_debug_stop_display(cls):
        cls.clear_buffer()
        cls._send_buffer[0] = CommandID.DEBUG_STOP_DISPLAY
        cls._bytes_set_last_time = 1
        return cls._send_buffer

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
    _data_length_idx = _DATA_LEN_IDX
    _data_idx = slice(_DATA_START, _DATA_END)
    _crc_idx = slice(_CRC16_START, _CRC16_END)

    _curr_id = 0
    _sequence_count = 0
    _curr_data_length = 0
    _crc_valid = False

    # specific buffer for file packet to be stored there for retrieval
    _file_recv_buffer = bytearray(_RECV_PCKT_BUF_SIZE)

    @classmethod
    def decode(cls, data):
        cls._recv_buffer = data

        # Verify packet size
        if len(data) < _TOTAL_PACKET_SIZE:
            return ErrorCodes.INVALID_PACKET

        # Verify CRC16 first - check entire packet including CRC
        cls._crc_valid = verify_crc16(cls._recv_buffer[:_TOTAL_PACKET_SIZE])
        if not cls._crc_valid:
            return ErrorCodes.INVALID_PACKET

        # header processing
        cls._curr_id = int(cls._recv_buffer[_CMD_ID_IDX])
        cls._sequence_count = int.from_bytes(cls._recv_buffer[cls._sequence_count_idx], byteorder=_BYTE_ORDER)
        cls._curr_data_length = int(cls._recv_buffer[cls._data_length_idx])

        # Validate data length doesn't exceed maximum payload
        if cls._curr_data_length > 240:
            return ErrorCodes.INVALID_PACKET

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
        err = int(cls._recv_buffer[cls._data_idx][1])
        if resp == ACK.ERROR:
            if err == PayloadErrorCodes.FILE_NOT_AVAILABLE:
                return ErrorCodes.FILE_NOT_AVAILABLE
            else:
                return ErrorCodes.INVALID_RESPONSE
        elif resp == ACK.SUCCESS:
            return ErrorCodes.OK

    @classmethod
    def decode_request_next_file(cls):

        Resp_RequestNextFilePacket.reset()

        if cls._curr_data_length <= 1:
            return ErrorCodes.INVALID_PACKET

        if int(cls._recv_buffer[cls._data_idx][0]) == ACK.ERROR:
            Resp_RequestNextFilePacket.error = int(cls._recv_buffer[cls._data_idx][1])
            if Resp_RequestNextFilePacket.error == PayloadErrorCodes.NO_MORE_PACKET_FOR_FILE:
                Resp_RequestNextFilePacket.no_more_packet_to_receive = True
                return ErrorCodes.NO_MORE_FILE_PACKET
            else:
                # TODO: maybe process other reason in the future but for now, we'll just re-ask the packet
                return ErrorCodes.INVALID_RESPONSE
        else:  # success
            Resp_RequestNextFilePacket.received_data_size = cls._curr_data_length
            Resp_RequestNextFilePacket.packet_nb = cls._sequence_count
            Resp_RequestNextFilePacket.received_data = cls._recv_buffer[cls._data_idx]
            return ErrorCodes.OK
