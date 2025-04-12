"""
Payload Commands and Responses Definitions

Author: Ibrahima Sory Sow
"""


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
    INVALID = 0x27


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
    INVALID_RESPONSE = 4
    TIMEOUT_SHUTDOWN = 5


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


class Resp_RequestImage:
    pass


class Resp_RequestNextFilePacket:
    pass


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
