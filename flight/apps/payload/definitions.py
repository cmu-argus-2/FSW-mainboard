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
    # Contains host's error codes
    OK = 0
    INVALID_COMMAND = 1
    COMMAND_ERROR_EXECUTION = 2
    INVALID_RESPONSE = 3
    TIMEOUT_SHUTDOWN = 4
