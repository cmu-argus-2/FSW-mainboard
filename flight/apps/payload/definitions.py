"""
Payload Commands and Responses Definitions

Author: Ibrahima Sory Sow
"""


class CommandID:
    PING_ACK = 0x00
    SHUTDOWN = 0x01
    SYNCHRONIZE_TIME = 0x02
    REQUEST_TELEMETRY = 0x03
    ENABLE_CAMERAS = 0x04
    DISABLE_CAMERAS = 0x05
    CAPTURE_IMAGES = 0x06
    START_CAPTURE_IMAGES_PERIODICALLY = 0x07
    STOP_CAPTURE_IMAGES = 0x08
    STORED_IMAGES = 0x09
    REQUEST_IMAGE = 0x0A
    DELETE_IMAGES = 0x0B
    RUN_OD = 0x0C
    PING_OD_STATUS = 0x0D
    DEBUG_DISPLAY_CAMERA = 0x0E
    DEBUG_STOP_DISPLAY = 0x0F


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
