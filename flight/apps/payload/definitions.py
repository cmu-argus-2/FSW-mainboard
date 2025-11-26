"""
Payload General Definitions
- Commands
- Requests
- Errors
- Data structures

Author: Ibrahima Sory Sow
"""

from core import logger


class ExternalRequest:
    """
    Represents a collection of external request codes used by the payload controller
    to perform specific tasks. These request codes serve as an abstraction
    layer, simplifying the interaction between the payload controller and
    the rest of the system.
    """

    NO_ACTION = 0x21
    TURN_ON = 0x22
    TURN_OFF = 0x23
    FORCE_POWER_OFF = 0x24
    REQUEST_IMAGE = 0x25
    CLEAR_STORAGE = 0x26
    REBOOT = 0x27
    INVALID = 0x28


class CommandID:
    PING_ACK = 0x00
    SHUTDOWN = 0x01
    REQUEST_TELEMETRY = 0x02
    ENABLE_CAMERAS = 0x03
    DISABLE_CAMERAS = 0x04
    CAPTURE_IMAGES = 0x05
    START_CAPTURE_IMAGES_PERIODICALLY = 0x06
    STOP_CAPTURE_IMAGES = 0x07
    REQUEST_STORAGE_INFO = 0x08
    REQUEST_IMAGE = 0x09
    REQUEST_NEXT_FILE_PACKET = 0x0A
    CLEAR_STORAGE = 0x0B
    PING_OD_STATUS = 0x0C
    RUN_OD = 0x0D
    REQUEST_OD_RESULT = 0x0E
    SYNCHRONIZE_TIME = 0x0F
    FULL_RESET = 0x10
    DEBUG_DISPLAY_CAMERA = 0x11
    DEBUG_STOP_DISPLAY = 0x12


class ACK:
    SUCCESS = 0x0A
    ERROR = 0x0B


class ErrorCodes:
    # Contains host's status codes
    NO_RESPONSE = 0
    OK = 1
    INVALID_COMMAND = 2
    COMMAND_ERROR_EXECUTION = 3
    INVALID_PACKET = 4
    INVALID_RESPONSE = 5
    TIMEOUT_SHUTDOWN = 6
    FILE_NOT_AVAILABLE = 7
    NO_MORE_FILE_PACKET = 8
    TIMEOUT_BOOT = 9
    TIMEOUT_SHUTDOWN = 10


class FileTransferType:
    NONE = 0
    IMAGE = 1
    OD_RESULT = 2


class PayloadErrorCodes:
    NONE = 0
    NO_MORE_PACKET_FOR_FILE = 5
    FILE_NOT_AVAILABLE = 7


class FileTransfer:
    packet_nb = 0
    in_progress = False
    transfer_type = FileTransferType.NONE
    last_transfer_type = FileTransferType.NONE

    @classmethod
    def reset(cls):
        cls.packet_nb = 0
        cls.in_progress = False
        cls.transfer_type = FileTransferType.NONE

    @classmethod
    def start_transfer(cls, transfer_type: FileTransferType):
        cls.in_progress = True
        cls.transfer_type = transfer_type
        cls.packet_nb = 1  # INFO: Payload expect the first packet to be 1

    @classmethod
    def ack_packet(cls):
        if cls.in_progress:
            cls.packet_nb += 1
        else:
            logger.error("No transfer in progress. Cannot acknowledge packet.")

    @classmethod
    def stop_transfer(cls):
        cls.last_transfer_type = cls.transfer_type
        cls.reset()


class ODStatusType:
    IDLE = 0
    DATA_COLLECTION = 1
    BATCH_OPT_IN_PROGRESS = 2
    RESULT_AVAILABLE = 3


class ODStatus:
    status = ODStatusType.IDLE
    continue_od_at_next_boot = False


class PayloadTM:  # Simple data structure holder
    # System part
    SYSTEM_TIME: int = 0
    SYSTEM_UPTIME: int = 0
    LAST_EXECUTED_CMD_TIME: int = 0
    LAST_EXECUTED_CMD_ID: int = 0
    PAYLOAD_STATE: int = 0
    ACTIVE_CAMERAS: int = 0
    CAPTURE_MODE: int = 0
    CAM_STATUS: list = [0] * 4
    IMU_STATUS: int = 0
    TASKS_IN_EXECUTION: int = 0
    DISK_USAGE: int = 0
    LATEST_ERROR: int = 0
    # Tegrastats part
    TEGRASTATS_PROCESS_STATUS: bool = False
    RAM_USAGE: int = 0
    SWAP_USAGE: int = 0
    ACTIVE_CORES: int = 0
    CPU_LOAD: list = [0] * 6
    GPU_FREQ: int = 0
    CPU_TEMP: int = 0
    GPU_TEMP: int = 0
    VDD_IN: int = 0
    VDD_CPU_GPU_CV: int = 0
    VDD_SOC: int = 0

    # utils var
    DATA_LENGTH_SIZE: int = 47

    @classmethod
    def print(cls):
        # ONLY for debugging purposes
        print(f"SYSTEM_TIME: {cls.SYSTEM_TIME}")
        print(f"SYSTEM_UPTIME: {cls.SYSTEM_UPTIME}")
        print(f"PAYLOAD_STATE: {cls.PAYLOAD_STATE}")
        print(f"ACTIVE_CAMERAS: {cls.ACTIVE_CAMERAS}")
        print(f"CAPTURE_MODE: {cls.CAPTURE_MODE}")
        print(f"CAM_STATUS: {cls.CAM_STATUS}")
        print(f"TASKS_IN_EXECUTION: {cls.TASKS_IN_EXECUTION}")
        print(f"DISK_USAGE: {cls.DISK_USAGE}")
        print(f"LATEST_ERROR: {cls.LATEST_ERROR}")
        print(f"LAST_EXECUTED_CMD_ID: {cls.LAST_EXECUTED_CMD_ID}")
        print(f"LAST_EXECUTED_CMD_TIME: {cls.LAST_EXECUTED_CMD_TIME}")
        print(f"TEGRASTATS_PROCESS_STATUS: {cls.TEGRASTATS_PROCESS_STATUS}")
        print(f"RAM_USAGE: {cls.RAM_USAGE}")
        print(f"SWAP_USAGE: {cls.SWAP_USAGE}")
        print(f"ACTIVE_CORES: {cls.ACTIVE_CORES}")
        print(f"CPU_LOAD: {cls.CPU_LOAD}")
        print(f"GPU_FREQ: {cls.GPU_FREQ}")
        print(f"CPU_TEMP: {cls.CPU_TEMP}")
        print(f"GPU_TEMP: {cls.GPU_TEMP}")
        print(f"VDD_IN: {cls.VDD_IN}")
        print(f"VDD_CPU_GPU_CV: {cls.VDD_CPU_GPU_CV}")
        print(f"VDD_SOC: {cls.VDD_SOC}")


# Decoder will fill those buffers
class Resp_EnableCameras:
    num_cam_activated = 0
    cam_status = [0, 0, 0, 0]

    @classmethod
    def reset(cls):
        cls.num_cam_activated = 0
        cls.cam_status = [0, 0, 0, 0]


class Resp_DisableCameras:
    num_cam_deactivated = 0
    cam_status = [0, 0, 0, 0]

    @classmethod
    def reset(cls):
        cls.num_cam_deactivated = 0
        cls.cam_status = [0, 0, 0, 0]


class RespCaptureImages:
    pass


class Resp_StartCaptureImagesPeriodically:
    pass


class Resp_StopCaptureImages:
    pass


class Resp_RequestStorageInfo:
    pass


class Resp_RequestNextFilePacket:
    received_data = bytearray(240)  # 240 bytes max payload per packet
    received_data_size = 0
    packet_nb = 0
    no_more_packet_to_receive = False
    error = PayloadErrorCodes.NONE

    @classmethod
    def reset(cls):
        cls.received_data = bytearray(240)
        cls.received_data_size = 0
        cls.no_more_packet_to_receive = False
        cls.packet_nb = 0
        cls.error = PayloadErrorCodes.NONE


class Resp_ClearStorage:
    pass


class Resp_PingODStatus:
    pass


class Resp_RunOD:
    pass


class Resp_RequestODResult:
    pass


class Resp_SynchronizeTime:
    pass
