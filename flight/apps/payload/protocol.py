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
- Byte 1-2: Sequence count
- Byte 3: Data length
- Byte 4-255: Data


Author: Ibrahima Sory Sow

"""

from definitions import CommandID, ErrorCodes

# Asymmetric sizes for send and receive buffers
_RECV_PCKT_BUF_SIZE = 256
_SEND_PCKT_BUF_SIZE = 32


class Encoder:
    _send_buffer = bytearray(_SEND_PCKT_BUF_SIZE)
    # TODO: clear buffer before each send

    @classmethod
    def encode_ping(cls):
        cls._send_buffer[0] = CommandID.PING_ACK
        return cls._send_buffer

    @classmethod
    def encode_shutdown(cls):
        cls._send_buffer[0] = CommandID.SHUTDOWN
        return cls._send_buffer

    @classmethod
    def encode_synchronize_time(cls):
        cls._send_buffer[0] = CommandID.SYNCHRONIZE_TIME
        return cls._send_buffer

    @classmethod
    def encode_request_telemetry(cls):
        cls._send_buffer[0] = CommandID.REQUEST_TELEMETRY
        return cls._send_buffer

    @classmethod
    def encode_enable_cameras(cls):
        cls._send_buffer[0] = CommandID.ENABLE_CAMERAS
        return cls._send_buffer

    @classmethod
    def encode_disable_cameras(cls):
        cls._send_buffer[0] = CommandID.DISABLE_CAMERAS
        return cls._send_buffer

    @classmethod
    def encode_capture_images(cls):
        cls._send_buffer[0] = CommandID.CAPTURE_IMAGES
        return cls._send_buffer

    @classmethod
    def encode_start_capture_images_periodically(cls):
        cls._send_buffer[0] = CommandID.START_CAPTURE_IMAGES_PERIODICALLY
        return cls._send_buffer

    @classmethod
    def encode_stop_capture_images(cls):
        cls._send_buffer[0] = CommandID.STOP_CAPTURE_IMAGES
        return cls._send_buffer

    @classmethod
    def encode_stored_images(cls):
        cls._send_buffer[0] = CommandID.STORED_IMAGES
        return cls._send_buffer

    @classmethod
    def encode_request_image(cls):
        cls._send_buffer[0] = CommandID.REQUEST_IMAGE
        return cls._send_buffer

    @classmethod
    def encode_delete_images(cls):
        cls._send_buffer[0] = CommandID.DELETE_IMAGES
        return cls._send_buffer

    @classmethod
    def encode_run_od(cls):
        cls._send_buffer[0] = CommandID.RUN_OD
        return cls._send_buffer

    @classmethod
    def encode_ping_od_status(cls):
        cls._send_buffer[0] = CommandID.PING_OD_STATUS
        return cls._send_buffer

    @classmethod
    def encode_debug_display_camera(cls):
        cls._send_buffer[0] = CommandID.DEBUG_DISPLAY_CAMERA
        return cls._send_buffer

    @classmethod
    def encode_debug_stop_display(cls):
        cls._send_buffer[0] = CommandID.DEBUG_STOP_DISPLAY
        return cls._send_buffer

    # Generic example without any checking
    @classmethod
    def encode_with_args(cls, command_id, *args):
        cls._send_buffer[0] = command_id
        for i, arg in enumerate(args, start=1):
            cls._send_buffer[i] = arg
        return cls._send_buffer


class Decoder:

    _recv_buffer = bytearray(_RECV_PCKT_BUF_SIZE)
    _sequence_count_idx = slice(1, 3)
    _data_length_idx = 3
    _data_idx = slice(4, 255)

    _curr_id = 0
    _curr_data_length = 0

    @classmethod
    def decode(cls, data):
        cls._recv_buffer = data
        print(cls._recv_buffer[0])
        # header processing
        cls._curr_id = cls._recv_buffer[0]
        # TODO: Seq count
        cls._curr_data_length = cls._recv_buffer[cls._data_length_idx]

        if cls._curr_id == CommandID.PING_ACK:
            return cls.decode_ping()
        elif cls._curr_id == CommandID.SHUTDOWN:
            return cls.decode_shutdown()
        elif cls._curr_id == CommandID.REQUEST_TELEMETRY:
            return cls.decode_request_telemetry()
        # rest is coming

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
