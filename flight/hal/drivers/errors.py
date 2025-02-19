from micropython import const

class Errors:

    ####SD Card/VFS Errors####
    SD_CARD_NO_ERROR = const(0x10)
    SD_CARD_NOT_INITIALIZED = const(0x11)
    VFS_NOT_INITIALIZED = const(0x12)

    ####IMU Errors####
    IMU_NOT_INITIALIZED = const(0x20)

    ####RTC Errors####
    RTC_NOT_INITIALIZED = const(0x30)

    ####GPS Errors####
    GPS_NOT_INITIALIZED = const(0x40)

    ####Radio Errors####
    RADIO_NOT_INITIALIZED = const(0x50)

    ####Power Monitor Errors####
    BOARD_POWER_MONITOR_NOT_INITIALIZED = const(0x160)

    

