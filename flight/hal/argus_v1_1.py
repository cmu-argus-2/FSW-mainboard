"""
Author: Harry, Thomas, Ibrahima
Description: This file contains the definition of the ArgusV1 class and its associated interfaces and components.
"""

from sys import path

import board
import neopixel
from busio import I2C, SPI, UART
from hal.cubesat import CubeSat
from hal.drivers.middleware.errors import Errors
from hal.drivers.middleware.middleware import Middleware
from micropython import const
from sdcardio import SDCard
from storage import VfsFat, mount


class ArgusV1Interfaces:
    """
    This class represents the interfaces used in the ArgusV1 module.
    """

    I2C1_SDA = board.SDA1    # PB12
    I2C1_SCL = board.SCL1    # PB13

    # Line may not be connected, try except sequence
    try:
        I2C1 = I2C(I2C1_SCL, I2C1_SDA)
    except Exception as e:
        print(e)
        I2C1 = None

    I2C2_SDA = board.SDA2    # PA22
    I2C2_SCL = board.SCL2    # PA23

    # Line may not be connected, try except sequence
    try:
        I2C2 = I2C(I2C2_SCL, I2C2_SDA)
    except Exception as e:
        print(e)
        I2C2 = None

    I2C3_SDA = board.SDA3    # PA16
    I2C3_SCL = board.SCL3    # PA17

    # Line may not be connected, try except sequence
    try:
        I2C3 = I2C(I2C3_SCL, I2C3_SDA)
    except Exception as e:
        print(e)
        I2C3 = None

    JET_SPI_SCK = board.JETSON_SCK    # PA5
    JET_SPI_MOSI = board.JETSON_MOSI    # PA4
    JET_SPI_MISO = board.JETSON_MISO    # PA6
    JET_SPI = SPI(JET_SPI_SCK, MOSI=JET_SPI_MOSI, MISO=JET_SPI_MISO)

    SPI_SCK = board.SCK    # PA13
    SPI_MOSI = board.MOSI    # PA12
    SPI_MISO = board.MISO    # PA14
    SPI = SPI(SPI_SCK, MOSI=SPI_MOSI, MISO=SPI_MISO)

    UART1_BAUD = const(9600)
    UART1_TX = board.TX    # PB2
    UART1_RX = board.RX    # PB3
    UART1 = UART(UART1_TX, UART1_RX, baudrate=UART1_BAUD)


class ArgusV1Components:
    """
    Represents the components used in the Argus V1 system.

    This class defines constants for various components such as GPS, battery,
    power monitor, Jetson power monitor, IMU, charger, torque coils,
    light sensors, radio, and SD card.
    """

    # I2C

    # BOARD POWER MONITOR
    BOARD_POWER_MONITOR_I2C = ArgusV1Interfaces.I2C1
    # 94(clash with X+ solar charging power monitor)
    BOARD_POWER_MONITOR_I2C_ADDRESS = const(0x4A)

    # CHARGER
    CHARGER_I2C = ArgusV1Interfaces.I2C1
    CHARGER_I2C_ADDRESS = const(0x6B)

    # IMU
    IMU_I2C = ArgusV1Interfaces.I2C1
    IMU_I2C_ADDRESS = const(0x69)

    # JETSON POWER MONITOR
    JETSON_POWER_MONITOR_I2C = ArgusV1Interfaces.I2C1
    JETSON_POWER_MONITOR_I2C_ADDRESS = const(0x45)    # 8A

    # X TORQUE COILS
    TORQUE_COILS_X_I2C = ArgusV1Interfaces.I2C1
    TORQUE_XP_I2C_ADDRESS = const(0x64)
    TORQUE_XM_I2C_ADDRESS = const(0x63)

    # X COIL DRIVER POWER MONITOR
    TORQUE_X_POWER_MONITOR_I2C = ArgusV1Interfaces.I2C1
    TORQUE_XP_POWER_MONITOR_I2C_ADDRESS = const(0x42)    # 84
    TORQUE_XM_POWER_MONITOR_I2C_ADDRESS = const(0x40)    # 80

    # X SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_X_POWER_MONITOR_I2C = ArgusV1Interfaces.I2C1
    SOLAR_CHARGING_XP_POWER_MONITOR_I2C_ADDRESS = const(0x49)  # 92
    SOLAR_CHARGING_XM_POWER_MONITOR_I2C_ADDRESS = const(0x48)  # 90

    # X LIGHT SENSOR
    LIGHT_SENSOR_X_I2C = ArgusV1Interfaces.I2C1
    LIGHT_SENSOR_XP_I2C_ADDRESS = const(0x45)
    LIGHT_SENSOR_XM_I2C_ADDRESS = const(0x44)

    # BATTERY BOARD FUEL GAUGE
    FUEL_GAUGE_I2C = ArgusV1Interfaces.I2C2
    FUEL_GAUGE_I2C_ADDRESS = const(0x6C)

    # Y TORQUE COILS
    TORQUE_COILS_Y_I2C = ArgusV1Interfaces.I2C2
    TORQUE_YP_I2C_ADDRESS = const(0x64)
    TORQUE_YM_I2C_ADDRESS = const(0x63)

    # Y COIL DRIVER POWER MONITOR
    TORQUE_Y_POWER_MONITOR_I2C = ArgusV1Interfaces.I2C2
    TORQUE_YP_POWER_MONITOR_I2C_ADDRESS = const(0x42)    # 84
    TORQUE_YM_POWER_MONITOR_I2C_ADDRESS = const(0x40)    # 80

    # Y SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_Y_POWER_MONITOR_I2C = ArgusV1Interfaces.I2C2
    SOLAR_CHARGING_YP_POWER_MONITOR_I2C_ADDRESS = const(0x49)    # 92
    SOLAR_CHARGING_YM_POWER_MONITOR_ENABLE = const(0x48)    # 90

    # Y LIGHT SENSOR
    LIGHT_SENSOR_Y_I2C = ArgusV1Interfaces.I2C2
    LIGHT_SENSOR_YP_I2C_ADDRESS = const(0x45)
    LIGHT_SENSOR_YM_I2C_ADDRESS = const(0x44)

    # RTC
    RTC_I2C = ArgusV1Interfaces.I2C3
    RTC_I2C_ADDRESS = const(0x68)

    # Z TORQUE COILS
    TORQUE_COILS_Z_I2C = ArgusV1Interfaces.I2C3
    TORQUE_ZP_I2C_ADDRESS = const(0x64)
    TORQUE_ZM_I2C_ADDRESS = const(0x63)

    # Z COIL DRIVER POWER MONITOR
    TORQUE_Z_POWER_MONITOR_I2C = ArgusV1Interfaces.I2C3
    TORQUE_ZP_POWER_MONITOR_I2C_ADDRESS = const(0x42)    # 84
    TORQUE_ZM_POWER_MONITOR_I2C_ADDRESS = const(0x40)    # 80

    # ZP SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_Z_POWER_MONITOR_I2C = ArgusV1Interfaces.I2C3
    SOLAR_CHARGING_ZP_POWER_MONITOR_I2C_ADDRESS = const(0x4A)    # 94

    # ZM LIGHT SENSOR
    LIGHT_SENSOR_Z_I2C = ArgusV1Interfaces.I2C3
    LIGHT_SENSOR_ZM_I2C_ADDRESS = const(0x44)    # Conflict with ZP

    # ZP SUN SENSOR
    SUN_SENSOR_ZP_I2C = ArgusV1Interfaces.I2C3
    SUN_SENSOR_ZP1_I2C_ADDRESS = const(0x44)    # Conflict with ZM
    SUN_SENSOR_ZP2_I2C_ADDRESS = const(0x45)
    SUN_SENSOR_ZP3_I2C_ADDRESS = const(0x46)
    SUN_SENSOR_ZP4_I2C_ADDRESS = const(0x47)

    # GPS
    GPS_UART = ArgusV1Interfaces.UART1
    GPS_ENABLE = board.GPS_EN    # PB1

    # RADIO
    RADIO_SPI = ArgusV1Interfaces.SPI
    # RADIO_CS = board.RF1_CS
    # RADIO_RESET = board.RF1_RST
    # RADIO_ENABLE = board.EN_RF
    # RADIO_DIO0 = board.RF1_IO0
    # RADIO_FREQ = 915.6

    # SD CARD
    SD_CARD_SPI = ArgusV1Interfaces.SPI
    SD_CARD_CS = board.SD_CS    # PA27
    SD_BAUD = const(4000000)    # 4 MHz

    # BURN WIRES
    BURN_WIRE_ENABLE = board.RELAY_A
    BURN_WIRE_XP = board.BURN1
    BURN_WIRE_XM = board.BURN2
    BURN_WIRE_YP = board.BURN3
    BURN_WIRE_YM = board.BURN4

    # NEOPIXEL
    NEOPIXEL_SDA = board.NEOPIXEL
    NEOPIXEL_N = const(1)  # Number of neopixels in chain
    NEOPIXEL_BRIGHTNESS = 0.2

    # PAYLOAD
    PAYLOAD_SPI = ArgusV1Interfaces.JET_SPI
    PAYLOAD_CS = board.JETSON_CS
    PAYLOAD_ENABLE = board.JETSON_EN

    # VFS
    VFS_MOUNT_POINT = "/sd"


class ArgusV1(CubeSat):
    """ArgusV1: Represents the Argus V1 CubeSat."""

    def __init__(self, enable_middleware: bool = False, debug: bool = False):
        """__init__: Initializes the Argus V1 CubeSat.

        :param enable_middleware: Enable middleware for the Argus V1 CubeSat
        """
        self.__middleware_enabled = enable_middleware
        self.__debug = debug

        super().__init__()

    ######################## BOOT SEQUENCE ########################

    def boot_sequence(self) -> list[int]:
        """boot_sequence: Boot sequence for the CubeSat."""
        error_list: list[int] = []

        # Create individual torque coil driver instances
        self.__torque_xp_driver = None
        self.__torque_xm_driver = None
        self.__torque_yp_driver = None
        self.__torque_ym_driver = None
        self.__torque_z_driver = None

        self.__state_flags_boot()  # Does not require error checking

        error_list.append(self.__sd_card_boot())
        error_list.append(self.__vfs_boot())
        error_list.append(self.__imu_boot())
        error_list.append(self.__rtc_boot())
        # error_list.append(self.__gps_boot())
        error_list.append(self.__board_power_monitor_boot())
        # error_list.append(self.__jetson_power_monitor_boot())
        error_list.append(self.__charger_boot())
        # error_list.append(self.__torque_interface_boot())
        # error_list.append(self.__light_sensor_xp_boot())
        # error_list.append(self.__light_sensor_xm_boot())
        # error_list.append(self.__light_sensor_yp_boot())
        # error_list.append(self.__light_sensor_ym_boot())
        # error_list.append(self.__light_sensor_zm_boot())
        # sun sensor here
        # error_list.append(self.__radio_boot())
        error_list.append(self.__neopixel_boot())
        # error_list.append(self.__burn_wire_boot())
        # error_list.append(self.__torque_xp_power_monitor_boot())
        # error_list.append(self.__torque_xm_power_monitor_boot())
        # error_list.append(self.__torque_yp_power_monitor_boot())
        # error_list.append(self.__torque_ym_power_monitor_boot())
        # error_list.append(self.__torque_zp_power_monitor_boot())
        # error_list.append(self.__torque_zm_power_monitor_boot())
        # error_list.append(self.__solar_xp_power_monitor_boot())
        # error_list.append(self.__solar_xm_power_monitor_boot())
        # error_list.append(self.__solar_yp_power_monitor_boot())
        # error_list.append(self.__solar_ym_power_monitor_boot())
        # error_list.append(self.__solar_zp_power_monitor_boot())

        error_list = [error for error in error_list if error != Errors.NOERROR]

        if self.__debug:
            print("Boot Errors:")
            print()
            for error in error_list:
                print(f"{Errors.diagnostic_to_string(error)}")
            print()

        self.__recent_errors = error_list

        return error_list

    def __state_flags_boot(self) -> None:
        """state_flags_boot: Boot sequence for the state flags"""
        from hal.drivers.stateflags import StateFlags

        self.__state_flags = StateFlags()

    def __gps_boot(self) -> list[int]:
        """GPS_boot: Boot sequence for the GPS

        :return: Error code if the GPS failed to initialize
        """
        try:
            from hal.drivers.gps import GPS

            gps1 = GPS(ArgusV1Components.GPS_UART,
                       ArgusV1Components.GPS_ENABLE)

            if self.__middleware_enabled:
                gps1 = Middleware(gps1)

            self.__gps = gps1
            self.__device_list.append(gps1)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.GPS_NOT_INITIALIZED

        return Errors.NOERROR

    def __board_power_monitor_boot(self) -> list[int]:
        """board_power_monitor_boot: Boot sequence for the battery power
           monitor

        :return: Error code if the battery power monitor failed to initialize
        """
        try:
            from hal.drivers.adm1176 import ADM1176

            board_power_monitor = ADM1176(
                ArgusV1Components.BOARD_POWER_MONITOR_I2C,
                ArgusV1Components.BOARD_POWER_MONITOR_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                board_power_monitor = Middleware(board_power_monitor)

            self.__board_power_monitor = board_power_monitor
            self.__device_list.append(board_power_monitor)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.ADM1176_NOT_INITIALIZED

        return Errors.NOERROR

    def __jetson_power_monitor_boot(self) -> list[int]:
        """jetson_power_monitor_boot: Boot sequence for the Jetson power 
           monitor

        :return: Error code if the Jetson power monitor failed to initialize
        """
        try:
            from hal.drivers.adm1176 import ADM1176

            jetson_monitor = ADM1176(
                ArgusV1Components.JETSON_POWER_MONITOR_I2C,
                ArgusV1Components.JETSON_POWER_MONITOR_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                jetson_monitor = Middleware(jetson_monitor)

            self.__jetson_monitor = jetson_monitor
            self.__device_list.append(jetson_monitor)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.ADM1176_NOT_INITIALIZED

        return Errors.NOERROR

    def __imu_boot(self) -> list[int]:
        """imu_boot: Boot sequence for the IMU

        :return: Error code if the IMU failed to initialize
        """
        try:
            from hal.drivers.bmx160 import BMX160

            imu = BMX160(
                ArgusV1Components.IMU_I2C,
                ArgusV1Components.IMU_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                imu = Middleware(imu)

            self.__imu = imu
            self.__device_list.append(imu)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.BMX160_NOT_INITIALIZED

        return Errors.NOERROR

    def __charger_boot(self) -> list[int]:
        """charger_boot: Boot sequence for the charger

        :return: Error code if the charger failed to initialize
        """
        try:
            from hal.drivers.bq25883 import BQ25883

            charger = BQ25883(
                ArgusV1Components.CHARGER_I2C,
                ArgusV1Components.CHARGER_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                charger = Middleware(charger)

            self.__charger = charger
            self.__device_list.append(charger)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.BQ25883_NOT_INITIALIZED

        return Errors.NOERROR

    def __torque_xp_boot(self) -> list[int]:
        """torque_xp_boot: Boot sequence for the torque driver in the x+ 
           direction

        :return: Error code if the torque driver failed to initialize
        """
        try:
            from hal.drivers.drv8830 import DRV8830

            torque_xp = DRV8830(
                ArgusV1Components.TORQUE_COILS_X_I2C,
                ArgusV1Components.TORQUE_XP_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                torque_xp = Middleware(torque_xp)

            self.__torque_xp_driver = torque_xp
            self.__device_list.append(torque_xp)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.DRV8830_NOT_INITIALIZED

        return Errors.NOERROR

    def __torque_xp_power_monitor_boot(self) -> list[int]:
        """torque_xp_power_monitor_boot: Boot sequence for the torque xp power
           monitor

        :return: Error code if the torque xp power monitor failed to initialize
        """
        try:
            from hal.drivers.adm1176 import ADM1176

            torque_xp_power_monitor = ADM1176(
                ArgusV1Components.TORQUE_X_POWER_MONITOR_I2C,
                ArgusV1Components.TORQUE_XP_POWER_MONITOR_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                torque_xp_power_monitor = Middleware(torque_xp_power_monitor)

            self.__torque_xp_power_monitor = torque_xp_power_monitor
            self.__device_list.append(torque_xp_power_monitor)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.ADM1176_NOT_INITIALIZED

        return Errors.NOERROR

    def __torque_xm_boot(self) -> list[int]:
        """torque_xm_boot: Boot sequence for the torque driver in the x-
           direction

        :return: Error code if the torque driver failed to initialize
        """
        try:
            from hal.drivers.drv8830 import DRV8830

            torque_xm = DRV8830(
                ArgusV1Components.TORQUE_COILS_X_I2C,
                ArgusV1Components.TORQUE_XM_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                torque_xm = Middleware(torque_xm)

            self.__torque_xm_driver = torque_xm
            self.__device_list.append(torque_xm)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.DRV8830_NOT_INITIALIZED

        return Errors.NOERROR

    def __torque_xm_power_monitor_boot(self) -> list[int]:
        """torque_xm_power_monitor_boot: Boot sequence for the torque xm power
           monitor

        :return: Error code if the torque xm power monitor failed to initialize
        """
        try:
            from hal.drivers.adm1176 import ADM1176

            torque_xm_power_monitor = ADM1176(
                ArgusV1Components.TORQUE_X_POWER_MONITOR_I2C,
                ArgusV1Components.TORQUE_XM_POWER_MONITOR_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                torque_xm_power_monitor = Middleware(torque_xm_power_monitor)

            self.__torque_xm_power_monitor = torque_xm_power_monitor
            self.__device_list.append(torque_xm_power_monitor)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.ADM1176_NOT_INITIALIZED

        return Errors.NOERROR

    def __torque_yp_boot(self) -> list[int]:
        """torque_yp_boot: Boot sequence for the torque driver in the y+ 
           direction

        :return: Error code if the torque driver failed to initialize
        """
        try:
            from hal.drivers.drv8830 import DRV8830

            torque_yp = DRV8830(
                ArgusV1Components.TORQUE_COILS_Y_I2C,
                ArgusV1Components.TORQUE_YP_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                torque_yp = Middleware(torque_yp)

            self.__torque_yp_driver = torque_yp
            self.__device_list.append(torque_yp)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.DRV8830_NOT_INITIALIZED

        return Errors.NOERROR

    def __torque_yp_power_monitor_boot(self) -> list[int]:
        """torque_yp_power_monitor_boot: Boot sequence for the torque yp power 
           monitor

        :return: Error code if the torque yp power monitor failed to initialize
        """
        try:
            from hal.drivers.adm1176 import ADM1176

            torque_yp_power_monitor = ADM1176(
                ArgusV1Components.TORQUE_Y_POWER_MONITOR_I2C,
                ArgusV1Components.TORQUE_YP_POWER_MONITOR_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                torque_yp_power_monitor = Middleware(torque_yp_power_monitor)

            self.__torque_yp_power_monitor = torque_yp_power_monitor
            self.__device_list.append(torque_yp_power_monitor)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.ADM1176_NOT_INITIALIZED

        return Errors.NOERROR

    def __torque_ym_boot(self) -> list[int]:
        """torque_ym_boot: Boot sequence for the torque driver in the y- 
           direction

        :return: Error code if the torque driver failed to initialize
        """
        try:
            from hal.drivers.drv8830 import DRV8830

            torque_ym = DRV8830(
                ArgusV1Components.TORQUE_COILS_Y_I2C,
                ArgusV1Components.TORQUE_YM_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                torque_ym = Middleware(torque_ym)

            self.__torque_ym_driver = torque_ym
            self.__device_list.append(torque_ym)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.DRV8830_NOT_INITIALIZED

        return Errors.NOERROR

    def __torque_ym_power_monitor_boot(self) -> list[int]:
        """torque_ym_power_monitor_boot: Boot sequence for the torque ym power 
           monitor

        :return: Error code if the torque ym power monitor failed to initialize
        """
        try:
            from hal.drivers.adm1176 import ADM1176

            torque_ym_power_monitor = ADM1176(
                ArgusV1Components.TORQUE_Y_POWER_MONITOR_I2C,
                ArgusV1Components.TORQUE_YM_POWER_MONITOR_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                torque_ym_power_monitor = Middleware(torque_ym_power_monitor)

            self.__torque_ym_power_monitor = torque_ym_power_monitor
            self.__device_list.append(torque_ym_power_monitor)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.ADM1176_NOT_INITIALIZED

        return Errors.NOERROR

    def __torque_zp_boot(self) -> list[int]:
        """torque_zp_boot: Boot sequence for the torque driver in the z 
           direction

        :return: Error code if the torque driver failed to initialize
        """
        try:
            from hal.drivers.drv8830 import DRV8830

            torque_zp = DRV8830(
                ArgusV1Components.TORQUE_COILS_Z_I2C,
                ArgusV1Components.TORQUE_ZP_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                torque_zp = Middleware(torque_zp)

            self.__torque_zp_driver = torque_zp
            self.__device_list.append(torque_zp)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.DRV8830_NOT_INITIALIZED

        return Errors.NOERROR

    def __torque_zp_power_monitor_boot(self) -> list[int]:
        """torque_zp_power_monitor_boot: Boot sequence for the torque zp power 
           monitor

        :return: Error code if the torque zp power monitor failed to initialize
        """
        try:
            from hal.drivers.adm1176 import ADM1176

            torque_zp_power_monitor = ADM1176(
                ArgusV1Components.TORQUE_Z_POWER_MONITOR_I2C,
                ArgusV1Components.TORQUE_ZP_POWER_MONITOR_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                torque_zp_power_monitor = Middleware(torque_zp_power_monitor)

            self.__torque_zp_power_monitor = torque_zp_power_monitor
            self.__device_list.append(torque_zp_power_monitor)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.ADM1176_NOT_INITIALIZED

        return Errors.NOERROR

    def __torque_zm_boot(self) -> list[int]:
        """torque_zm_boot: Boot sequence for the torque driver in the z 
           direction

        :return: Error code if the torque driver failed to initialize
        """
        try:
            from hal.drivers.drv8830 import DRV8830

            torque_zm = DRV8830(
                ArgusV1Components.TORQUE_COILS_Z_I2C,
                ArgusV1Components.TORQUE_ZM_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                torque_zm = Middleware(torque_zm)

            self.__torque_zm_driver = torque_zm
            self.__device_list.append(torque_zm)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.DRV8830_NOT_INITIALIZED

        return Errors.NOERROR

    def __torque_zm_power_monitor_boot(self) -> list[int]:
        """torque_zm_power_monitor_boot: Boot sequence for the torque zm power 
           monitor

        :return: Error code if the torque zm power monitor failed to initialize
        """
        try:
            from hal.drivers.adm1176 import ADM1176

            torque_zm_power_monitor = ADM1176(
                ArgusV1Components.TORQUE_Z_POWER_MONITOR_I2C,
                ArgusV1Components.TORQUE_ZM_POWER_MONITOR_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                torque_zm_power_monitor = Middleware(torque_zm_power_monitor)

            self.__torque_zm_power_monitor = torque_zm_power_monitor
            self.__device_list.append(torque_zm_power_monitor)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.ADM1176_NOT_INITIALIZED

        return Errors.NOERROR

    def __torque_interface_boot(self) -> list[int]:
        """torque_interface_boot: Boot sequence for the torque interface

        :return: Error code if the torque interface failed to initialize
        """
        error_list: list[int] = []

        error_list.append(self.__torque_xp_boot())
        error_list.append(self.__torque_xm_boot())
        error_list.append(self.__torque_yp_boot())
        error_list.append(self.__torque_ym_boot())
        error_list.append(self.__torque_zp_boot())
        error_list.append(self.__torque_zm_boot())

        from hal.drivers.torque_coil import TorqueInterface

        # X direction
        try:
            torque_interface = TorqueInterface(
                self.__torque_xp_driver, self.__torque_xm_driver)
            self.__torque_x = torque_interface
        except Exception as e:
            if self.__debug:
                raise e

        # Y direction
        try:
            torque_interface = TorqueInterface(
                self.__torque_yp_driver, self.__torque_ym_driver)
            self.__torque_y = torque_interface
        except Exception as e:
            if self.__debug:
                raise e

        # Z direction
        try:
            torque_interface = TorqueInterface(
                self.__torque_zp_driver, self.__torque_zm_driver)
            self.__torque_z = torque_interface
        except Exception as e:
            if self.__debug:
                raise e

        return error_list

    def __light_sensor_xp_boot(self) -> list[int]:
        """light_sensor_xp_boot: Boot sequence for the light sensor in the x+ 
           direction

        :return: Error code if the light sensor failed to initialize
        """
        try:
            from hal.drivers.opt4001 import OPT4001

            light_sensor_xp = OPT4001(
                ArgusV1Components.LIGHT_SENSORS_I2C,
                ArgusV1Components.LIGHT_SENSOR_XP_I2C_ADDRESS,
                conversion_time=ArgusV1Components.LIGHT_SENSOR_CONVERSION_TIME,
            )

            if self.__middleware_enabled:
                light_sensor_xp = Middleware(light_sensor_xp)

            self.__light_sensor_xp = light_sensor_xp
            self.__device_list.append(light_sensor_xp)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.OPT4001_NOT_INITIALIZED

        return Errors.NOERROR

    def __light_sensor_xm_boot(self) -> list[int]:
        """light_sensor_xm_boot: Boot sequence for the light sensor in the x- 
           direction

        :return: Error code if the light sensor failed to initialize
        """
        try:
            from hal.drivers.opt4001 import OPT4001

            light_sensor_xm = OPT4001(
                ArgusV1Components.LIGHT_SENSORS_I2C,
                ArgusV1Components.LIGHT_SENSOR_XM_I2C_ADDRESS,
                conversion_time=ArgusV1Components.LIGHT_SENSOR_CONVERSION_TIME,
            )

            if self.__middleware_enabled:
                light_sensor_xm = Middleware(light_sensor_xm)

            self.__light_sensor_xm = light_sensor_xm
            self.__device_list.append(light_sensor_xm)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.OPT4001_NOT_INITIALIZED

        return Errors.NOERROR

    def __light_sensor_yp_boot(self) -> list[int]:
        """light_sensor_yp_boot: Boot sequence for the light sensor in the y+ 
           direction

        :return: Error code if the light sensor failed to initialize
        """
        try:
            from hal.drivers.opt4001 import OPT4001

            light_sensor_yp = OPT4001(
                ArgusV1Components.LIGHT_SENSORS_I2C,
                ArgusV1Components.LIGHT_SENSOR_YP_I2C_ADDRESS,
                conversion_time=ArgusV1Components.LIGHT_SENSOR_CONVERSION_TIME,
            )

            if self.__middleware_enabled:
                light_sensor_yp = Middleware(light_sensor_yp)

            self.__light_sensor_yp = light_sensor_yp
            self.__device_list.append(light_sensor_yp)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.OPT4001_NOT_INITIALIZED

        return Errors.NOERROR

    def __light_sensor_ym_boot(self) -> list[int]:
        """light_sensor_ym_boot: Boot sequence for the light sensor in the y- 
           direction

        :return: Error code if the light sensor failed to initialize
        """
        try:
            from hal.drivers.opt4001 import OPT4001

            light_sensor_ym = OPT4001(
                ArgusV1Components.LIGHT_SENSORS_I2C,
                ArgusV1Components.LIGHT_SENSOR_YM_I2C_ADDRESS,
                conversion_time=ArgusV1Components.LIGHT_SENSOR_CONVERSION_TIME,
            )

            if self.__middleware_enabled:
                light_sensor_ym = Middleware(light_sensor_ym)

            self.__light_sensor_ym = light_sensor_ym
            self.__device_list.append(light_sensor_ym)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.OPT4001_NOT_INITIALIZED

        return Errors.NOERROR

    def __light_sensor_zm_boot(self) -> list[int]:
        """light_sensor_zm_boot: Boot sequence for the light sensor in the z+ 
           direction

        :return: Error code if the light sensor failed to initialize
        """
        try:
            from hal.drivers.opt4001 import OPT4001

            light_sensor_zm = OPT4001(
                ArgusV1Components.LIGHT_SENSORS_I2C,
                ArgusV1Components.LIGHT_SENSOR_ZM_I2C_ADDRESS,
                conversion_time=ArgusV1Components.LIGHT_SENSOR_CONVERSION_TIME,
            )

            if self.__middleware_enabled:
                light_sensor_zm = Middleware(light_sensor_zm)

            self.__light_sensor_zm = light_sensor_zm
            self.__device_list.append(light_sensor_zm)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.OPT4001_NOT_INITIALIZED

        return Errors.NOERROR

    def __solar_charging_xp_power_monitor_boot(self) -> list[int]:
        """solar_charging_xp_power_monitor_boot: Boot sequence for the solar 
           charging xp power monitor

        :return: Error code if the solar charging xp power monitor failed to 
                 initialize
        """
        try:
            from hal.drivers.adm1176 import ADM1176

            solar_charging_xp_power_monitor = ADM1176(
                ArgusV1Components.SOLAR_CHARGING_X_POWER_MONITOR_I2C,
                ArgusV1Components.SOLAR_CHARGING_XP_POWER_MONITOR_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                solar_charging_xp_power_monitor = Middleware(
                    solar_charging_xp_power_monitor)

            self.__solar_charging_xp_power_monitor = solar_charging_xp_power_monitor
            self.__device_list.append(solar_charging_xp_power_monitor)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.ADM1176_NOT_INITIALIZED

        return Errors.NOERROR

    def __solar_charging_xm_power_monitor_boot(self) -> list[int]:
        """solar_charging_xm_power_monitor_boot: Boot sequence for the solar 
           charging xm power monitor

        :return: Error code if the solar charging xm power monitor failed to 
                 initialize
        """
        try:
            from hal.drivers.adm1176 import ADM1176

            solar_charging_xm_power_monitor = ADM1176(
                ArgusV1Components.SOLAR_CHARGING_X_POWER_MONITOR_I2C,
                ArgusV1Components.SOLAR_CHARGING_XM_POWER_MONITOR_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                solar_charging_xm_power_monitor = Middleware(
                    solar_charging_xm_power_monitor)

            self.__solar_charging_xm_power_monitor = solar_charging_xm_power_monitor
            self.__device_list.append(solar_charging_xm_power_monitor)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.ADM1176_NOT_INITIALIZED

        return Errors.NOERROR

    def __solar_charging_yp_power_monitor_boot(self) -> list[int]:
        """solar_charging_yp_power_monitor_boot: Boot sequence for the solar 
           charging yp power monitor

        :return: Error code if the solar charging yp power monitor failed to 
                 initialize
        """
        try:
            from hal.drivers.adm1176 import ADM1176

            solar_charging_yp_power_monitor = ADM1176(
                ArgusV1Components.SOLAR_CHARGING_Y_POWER_MONITOR_I2C,
                ArgusV1Components.SOLAR_CHARGING_YP_POWER_MONITOR_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                solar_charging_yp_power_monitor = Middleware(
                    solar_charging_yp_power_monitor)

            self.__solar_charging_yp_power_monitor = solar_charging_yp_power_monitor
            self.__device_list.append(solar_charging_yp_power_monitor)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.ADM1176_NOT_INITIALIZED

        return Errors.NOERROR

    def __solar_charging_ym_power_monitor_boot(self) -> list[int]:
        """solar_charging_ym_power_monitor_boot: Boot sequence for the solar 
           charging ym power monitor

        :return: Error code if the solar charging ym power monitor failed to 
                 initialize
        """
        try:
            from hal.drivers.adm1176 import ADM1176

            solar_charging_ym_power_monitor = ADM1176(
                ArgusV1Components.SOLAR_CHARGING_Y_POWER_MONITOR_I2C,
                ArgusV1Components.SOLAR_CHARGING_YM_POWER_MONITOR_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                solar_charging_ym_power_monitor = Middleware(
                    solar_charging_ym_power_monitor)

            self.__solar_charging_ym_power_monitor = solar_charging_ym_power_monitor
            self.__device_list.append(solar_charging_ym_power_monitor)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.ADM1176_NOT_INITIALIZED

        return Errors.NOERROR

    def __solar_charging_zp_power_monitor_boot(self) -> list[int]:
        """solar_charging_zp_power_monitor_boot: Boot sequence for the solar 
           charging zp power monitor

        :return: Error code if the solar charging zp power monitor failed to 
                 initialize
        """
        try:
            from hal.drivers.adm1176 import ADM1176

            solar_charging_zp_power_monitor = ADM1176(
                ArgusV1Components.SOLAR_CHARGING_Z_POWER_MONITOR_I2C,
                ArgusV1Components.SOLAR_CHARGING_ZP_POWER_MONITOR_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                solar_charging_zp_power_monitor = Middleware(
                    solar_charging_zp_power_monitor)

            self.__solar_charging_zp_power_monitor = solar_charging_zp_power_monitor
            self.__device_list.append(solar_charging_zp_power_monitor)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.ADM1176_NOT_INITIALIZED

        return Errors.NOERROR

    def __radio_boot(self) -> list[int]:
        """radio_boot: Boot sequence for the radio

        :return: Error code if the radio failed to initialize
        """
        try:
            from hal.drivers.rfm9x import RFM9x

            radio = RFM9x(
                ArgusV1Components.RADIO_SPI,
                ArgusV1Components.RADIO_CS,
                ArgusV1Components.RADIO_DIO0,
                ArgusV1Components.RADIO_RESET,
                ArgusV1Components.RADIO_ENABLE,
                ArgusV1Components.RADIO_FREQ,
            )

            if self.__middleware_enabled:
                radio = Middleware(radio)

            self.__radio = radio
            self.__device_list.append(radio)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.RFM9X_NOT_INITIALIZED

        return Errors.NOERROR

    def __rtc_boot(self) -> list[int]:
        """rtc_boot: Boot sequence for the RTC

        :return: Error code if the RTC failed to initialize
        """
        try:
            from hal.drivers.pcf8523 import PCF8523

            rtc = PCF8523(
                ArgusV1Components.RTC_I2C,
                ArgusV1Components.RTC_I2C_ADDRESS
            )

            if self.__middleware_enabled:
                rtc = Middleware(rtc)

            self.__rtc = rtc
            self.__device_list.append(rtc)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.PCF8523_NOT_INITIALIZED

        return Errors.NOERROR

    def __neopixel_boot(self) -> list[int]:
        """neopixel_boot: Boot sequence for the neopixel"""
        try:
            np = neopixel.NeoPixel(
                ArgusV1Components.NEOPIXEL_SDA,
                ArgusV1Components.NEOPIXEL_N,
                brightness=ArgusV1Components.NEOPIXEL_BRIGHTNESS,
                pixel_order=neopixel.GRB,
            )
            self.__neopixel = np
            self.__device_list.append(neopixel)
            self.append_device(neopixel)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.NEOPIXEL_NOT_INITIALIZED

        return Errors.NOERROR

    def __sd_card_boot(self) -> list[int]:
        """sd_card_boot: Boot sequence for the SD card"""
        try:
            sd_card = SDCard(
                ArgusV1Components.SD_CARD_SPI,
                ArgusV1Components.SD_CARD_CS,
                ArgusV1Components.SD_BAUD,
            )
            self.__sd_card = sd_card
            self.append_device(sd_card)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.SDCARD_NOT_INITIALIZED

        return Errors.NOERROR

    def __vfs_boot(self) -> list[int]:
        """vfs_boot: Boot sequence for the VFS"""
        if self.__sd_card is None:
            return Errors.SDCARD_NOT_INITIALIZED

        try:
            vfs = VfsFat(self.__sd_card)

            mount(vfs, ArgusV1Components.VFS_MOUNT_POINT)
            path.append(ArgusV1Components.VFS_MOUNT_POINT)

            path.append(ArgusV1Components.VFS_MOUNT_POINT)
            self.__vfs = vfs
        except Exception as e:
            if self.__debug:
                raise e
            raise e

            return Errors.VFS_NOT_INITIALIZED

        return Errors.NOERROR

    def __burn_wire_boot(self) -> list[int]:
        """burn_wire_boot: Boot sequence for the burn wires"""
        try:
            from hal.drivers.burnwire import BurnWires

            burn_wires = BurnWires(
                ArgusV1Components.BURN_WIRE_ENABLE,
                ArgusV1Components.BURN_WIRE_XP,
                ArgusV1Components.BURN_WIRE_XM,
                ArgusV1Components.BURN_WIRE_YP,
                ArgusV1Components.BURN_WIRE_YM,
            )

            if self.__middleware_enabled:
                burn_wires = Middleware(burn_wires)

            self.__burn_wires = burn_wires
            self.append_device(burn_wires)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.BURNWIRES_NOT_INITIALIZED

        return Errors.NOERROR

    def __fuel_gauge_boot(self) -> list[int]:
        """fuel_gauge_boot: Boot sequence for the fuel gauge"""
        try:
            from hal.drivers.max17205 import MAX17205

            fuel_gauge = MAX17205(
                ArgusV1Components.FUEL_GAUGE_I2C,
                ArgusV1Components.FUEL_GAUGE_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                fuel_gauge = Middleware(fuel_gauge)

            self.__fuel_gauge = fuel_gauge
            self.append_device(fuel_gauge)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.MAX17205_NOT_INITIALIZED

        return Errors.NOERROR
    
    ######################## DIAGNOSTICS ########################
    def __get_device_diagnostic_error(self, device) -> list[int]:  # noqa: C901
        """__get_device_diagnostic_error: Get the error code for a device that 
           failed to initialize"""
        # Convert device to the wrapped instance
        if isinstance(device, Middleware):
            device = device.get_instance()

        if device is self.RTC:
            return Errors.DIAGNOSTICS_ERROR_RTC
        elif device is self.GPS:
            return Errors.DIAGNOSTICS_ERROR_GPS
        elif device is self.BOARD_POWER_MONITOR:
            return Errors.DIAGNOSTICS_ERROR_BOARD_POWER_MONITOR
        elif device is self.JETSON_POWER_MONITOR:
            return Errors.DIAGNOSTICS_ERROR_JETSON_POWER_MONITOR
        elif device is self.IMU:
            return Errors.DIAGNOSTICS_ERROR_IMU
        elif device is self.CHARGER:
            return Errors.DIAGNOSTICS_ERROR_CHARGER
        elif device is self.__torque_xp_driver:
            return Errors.DIAGNOSTICS_ERROR_TORQUE_XP
        elif device is self.__torque_xm_driver:
            return Errors.DIAGNOSTICS_ERROR_TORQUE_XM
        elif device is self.__torque_yp_driver:
            return Errors.DIAGNOSTICS_ERROR_TORQUE_YP
        elif device is self.__torque_ym_driver:
            return Errors.DIAGNOSTICS_ERROR_TORQUE_YM
        elif device is self.__torque_z_driver:
            return Errors.DIAGNOSTICS_ERROR_TORQUE_Z
        elif device is self.LIGHT_SENSOR_XP:
            return Errors.DIAGNOSTICS_ERROR_LIGHT_SENSOR_XP
        elif device is self.LIGHT_SENSOR_XM:
            return Errors.DIAGNOSTICS_ERROR_LIGHT_SENSOR_XM
        elif device is self.LIGHT_SENSOR_YP:
            return Errors.DIAGNOSTICS_ERROR_LIGHT_SENSOR_YP
        elif device is self.LIGHT_SENSOR_YM:
            return Errors.DIAGNOSTICS_ERROR_LIGHT_SENSOR_YM
        elif device is self.LIGHT_SENSOR_ZM:
            return Errors.DIAGNOSTICS_ERROR_LIGHT_SENSOR_ZM
        elif device is self.RADIO:
            return Errors.DIAGNOSTICS_ERROR_RADIO
        elif device is self.NEOPIXEL:
            return Errors.DIAGNOSTICS_ERROR_NEOPIXEL
        elif device is self.BURN_WIRES:
            return Errors.DIAGNOSTICS_ERROR_BURN_WIRES
        else:
            return Errors.DIAGNOSTICS_ERROR_UNKNOWN

    def run_system_diagnostics(self) -> list[int] | None:
        """run_diagnostic_test: Run all diagnostics across all components

        :return: A list of error codes if any errors are present
        """
        error_list: list[int] = []

        for device in self.device_list:
            try:
                # Enable the devices that are resetable
                if device.resetable:
                    device.enable()

                # Concancate the error list from running diagnostics
                error_list += device.run_diagnostics()

                # Disable the devices that are resetable
                if device.resetable:
                    device.disable()
            except Exception:
                error_list.append(self.__get_device_diagnostic_error(device))
                continue

        error_list = [err for err in error_list if err != Errors.NOERROR]
        error_list = list(set(error_list))  # Remove duplicate errors

        self.__recent_errors = error_list

        return error_list
