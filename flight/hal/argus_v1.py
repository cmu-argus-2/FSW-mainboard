"""
File: argus_v1.py
Author: Harry
Description: This file contains the definition of the ArgusV1 class and its associated interfaces and components.
"""

from sys import path

import board
import neopixel
from busio import I2C, SPI, UART
from hal.cubesat import CubeSat
from hal.drivers.adm1176 import ADM1176
from hal.drivers.bmx160 import BMX160
from hal.drivers.bq25883 import BQ25883
from hal.drivers.burnwire import BurnWires
from hal.drivers.drv8830 import DRV8830
from hal.drivers.gps import GPS
from hal.drivers.middleware.errors import Errors
from hal.drivers.middleware.middleware import Middleware
from hal.drivers.opt4001 import OPT4001
from hal.drivers.payload import PayloadUART
from hal.drivers.pcf8523 import PCF8523
from hal.drivers.rfm9x import RFM9x
from hal.drivers.stateflags import StateFlags
from hal.drivers.torque_coil import TorqueInterface
from micropython import const
from sdcardio import SDCard
from storage import VfsFat, mount


class ArgusV1Interfaces:
    """
    This class represents the interfaces used in the ArgusV1 module.
    """

    I2C1_SDA = board.SDA
    I2C1_SCL = board.SCL
    I2C1 = I2C(I2C1_SCL, I2C1_SDA)

    I2C2_SDA = board.SDA2
    I2C2_SCL = board.SCL2
    I2C2 = I2C(I2C2_SCL, I2C2_SDA)

    SPI_SCK = board.SCK
    SPI_MOSI = board.MOSI
    SPI_MISO = board.MISO
    SPI = SPI(SPI_SCK, MOSI=SPI_MOSI, MISO=SPI_MISO)

    UART1_BAUD = const(9600)
    UART1_TX = board.TX
    UART1_RX = board.RX
    UART1 = UART(UART1_TX, UART1_RX, baudrate=UART1_BAUD)

    UART2_BAUD = const(57600)
    UART2_RECEIVE_BUF_SIZE = const(256)
    UART2_TX = board.JET_TX
    UART2_RX = board.JET_RX
    UART2 = UART(
        UART2_TX,
        UART2_RX,
        baudrate=UART2_BAUD,
        receiver_buffer_size=UART2_RECEIVE_BUF_SIZE,
    )


class ArgusV1Components:
    """
    Represents the components used in the Argus V1 system.

    This class defines constants for various components such as GPS, battery power monitor,
    Jetson power monitor, IMU, charger, torque coils, light sensors, radio, and SD card.
    """

    # GPS
    GPS_UART = ArgusV1Interfaces.UART1
    GPS_ENABLE = board.EN_GPS

    # BATTERY POWER MONITOR
    BATTERY_POWER_MONITOR_I2C = ArgusV1Interfaces.I2C1
    BATTERY_POWER_MONITOR_I2C_ADDRESS = const(0x4A)

    # JETSON POWER MONITOR
    JETSON_POWER_MONITOR_I2C = ArgusV1Interfaces.I2C1
    JETSON_POWER_MONITOR_I2C_ADDRESS = const(0xCA)

    # IMU
    IMU_I2C = ArgusV1Interfaces.I2C1
    IMU_I2C_ADDRESS = const(0x69)
    IMU_ENABLE = board.EN_IMU

    # CHARGER
    CHARGER_I2C = ArgusV1Interfaces.I2C1
    CHARGER_I2C_ADDRESS = const(0x6B)

    # TORQUE COILS
    TORQUE_COILS_I2C = ArgusV1Interfaces.I2C2
    TORQUE_XP_I2C_ADDRESS = const(0x60)
    TORQUE_XM_I2C_ADDRESS = const(0x62)
    TORQUE_YP_I2C_ADDRESS = const(0x63)
    TORQUE_YM_I2C_ADDRESS = const(0x64)
    TORQUE_Z_I2C_ADDRESS = const(0x66)

    # SUN SENSORS
    LIGHT_SENSORS_I2C = ArgusV1Interfaces.I2C2
    LIGHT_SENSOR_XP_I2C_ADDRESS = const(0x44)
    LIGHT_SENSOR_XM_I2C_ADDRESS = const(0x45)
    LIGHT_SENSOR_YP_I2C_ADDRESS = const(0x46)
    LIGHT_SENSOR_YM_I2C_ADDRESS = const(0x47)
    LIGHT_SENSOR_ZM_I2C_ADDRESS = const(0x48)
    LIGHT_SENSOR_CONVERSION_TIME = 0b0000

    # RADIO
    RADIO_SPI = ArgusV1Interfaces.SPI
    RADIO_CS = board.RF1_CS
    RADIO_RESET = board.RF1_RST
    RADIO_ENABLE = board.EN_RF
    RADIO_DIO0 = board.RF1_IO0
    RADIO_FREQ = 433.0
    # RADIO_FREQ = 915.6

    # SD CARD
    SD_CARD_SPI = ArgusV1Interfaces.SPI
    SD_CARD_CS = board.SD_CS
    SD_BAUD = const(4000000)  # 4 MHz

    # BURN WIRES
    BURN_WIRE_ENABLE = board.RELAY_A
    BURN_WIRE_XP = board.BURN1
    BURN_WIRE_XM = board.BURN2
    BURN_WIRE_YP = board.BURN3
    BURN_WIRE_YM = board.BURN4

    # RTC
    RTC_I2C = ArgusV1Interfaces.I2C1
    RTC_I2C_ADDRESS = const(0x68)

    # NEOPIXEL
    NEOPIXEL_SDA = board.NEOPIXEL
    NEOPIXEL_N = const(1)  # Number of neopixels in chain
    NEOPIXEL_BRIGHTNESS = 0.2

    # PAYLOAD
    PAYLOAD_UART = ArgusV1Interfaces.UART2
    PAYLOAD_ENABLE = board.EN_JET

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

        error_list += self.__sd_card_boot()
        error_list += self.__vfs_boot()
        error_list += self.__imu_boot()
        error_list += self.__rtc_boot()
        error_list += self.__gps_boot()
        error_list += self.__battery_power_monitor_boot()
        error_list += self.__jetson_power_monitor_boot()
        error_list += self.__charger_boot()
        error_list += self.__torque_interface_boot()
        error_list += self.__light_sensor_xp_boot()
        error_list += self.__light_sensor_xm_boot()
        error_list += self.__light_sensor_yp_boot()
        error_list += self.__light_sensor_ym_boot()
        error_list += self.__light_sensor_zm_boot()
        error_list += self.__radio_boot()
        error_list += self.__neopixel_boot()
        error_list += self.__burn_wire_boot()
        error_list += self.__payload_uart_boot()

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
        self.__state_flags = StateFlags()

    def __gps_boot(self) -> list[int]:
        """GPS_boot: Boot sequence for the GPS

        :return: Error code if the GPS failed to initialize
        """
        try:
            gps1 = GPS(ArgusV1Components.GPS_UART, ArgusV1Components.GPS_ENABLE)

            if self.__middleware_enabled:
                gps1 = Middleware(gps1)

            self.__gps = gps1
            self.__device_list.append(gps1)
        except Exception as e:
            if self.__debug:
                raise e

            return [Errors.GPS_NOT_INITIALIZED]

        return [Errors.NOERROR]

    def __battery_power_monitor_boot(self) -> list[int]:
        """battery_power_monitor_boot: Boot sequence for the battery power monitor

        :return: Error code if the battery power monitor failed to initialize
        """
        try:
            battery_monitor = ADM1176(
                ArgusV1Components.BATTERY_POWER_MONITOR_I2C,
                ArgusV1Components.BATTERY_POWER_MONITOR_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                battery_monitor = Middleware(battery_monitor)

            self.__battery_monitor = battery_monitor
            self.__device_list.append(battery_monitor)
        except Exception as e:
            if self.__debug:
                raise e

            return [Errors.ADM1176_NOT_INITIALIZED]

        return [Errors.NOERROR]

    def __jetson_power_monitor_boot(self) -> list[int]:
        """jetson_power_monitor_boot: Boot sequence for the Jetson power monitor

        :return: Error code if the Jetson power monitor failed to initialize
        """
        try:
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

            return [Errors.ADM1176_NOT_INITIALIZED]

        return [Errors.NOERROR]

    def __imu_boot(self) -> list[int]:
        """imu_boot: Boot sequence for the IMU

        :return: Error code if the IMU failed to initialize
        """
        try:
            imu = BMX160(
                ArgusV1Components.IMU_I2C,
                ArgusV1Components.IMU_I2C_ADDRESS,
                ArgusV1Components.IMU_ENABLE,
            )

            if self.__middleware_enabled:
                imu = Middleware(imu)

            self.__imu = imu
            self.__device_list.append(imu)
        except Exception as e:
            if self.__debug:
                raise e

            return [Errors.BMX160_NOT_INITIALIZED]

        return [Errors.NOERROR]

    def __charger_boot(self) -> list[int]:
        """charger_boot: Boot sequence for the charger

        :return: Error code if the charger failed to initialize
        """
        try:
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

            return [Errors.BQ25883_NOT_INITIALIZED]

        return [Errors.NOERROR]

    def __torque_xp_boot(self) -> list[int]:
        """torque_xp_boot: Boot sequence for the torque driver in the x+ direction

        :return: Error code if the torque driver failed to initialize
        """
        try:
            torque_xp = DRV8830(
                ArgusV1Components.TORQUE_COILS_I2C,
                ArgusV1Components.TORQUE_XP_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                torque_xp = Middleware(torque_xp)

            self.__torque_xp_driver = torque_xp
            self.__device_list.append(torque_xp)
        except Exception as e:
            if self.__debug:
                raise e

            return [Errors.DRV8830_NOT_INITIALIZED]

        return [Errors.NOERROR]

    def __torque_xm_boot(self) -> list[int]:
        """torque_xm_boot: Boot sequence for the torque driver in the x- direction

        :return: Error code if the torque driver failed to initialize
        """
        try:
            torque_xm = DRV8830(
                ArgusV1Components.TORQUE_COILS_I2C,
                ArgusV1Components.TORQUE_XM_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                torque_xm = Middleware(torque_xm)

            self.__torque_xm_driver = torque_xm
            self.__device_list.append(torque_xm)
        except Exception as e:
            if self.__debug:
                raise e

            return [Errors.DRV8830_NOT_INITIALIZED]

        return [Errors.NOERROR]

    def __torque_yp_boot(self) -> list[int]:
        """torque_yp_boot: Boot sequence for the torque driver in the y+ direction

        :return: Error code if the torque driver failed to initialize
        """
        try:
            torque_yp = DRV8830(
                ArgusV1Components.TORQUE_COILS_I2C,
                ArgusV1Components.TORQUE_YP_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                torque_yp = Middleware(torque_yp)

            self.__torque_yp_driver = torque_yp
            self.__device_list.append(torque_yp)
        except Exception as e:
            if self.__debug:
                raise e

            return [Errors.DRV8830_NOT_INITIALIZED]

        return [Errors.NOERROR]

    def __torque_ym_boot(self) -> list[int]:
        """torque_ym_boot: Boot sequence for the torque driver in the y- direction

        :return: Error code if the torque driver failed to initialize
        """
        try:
            torque_ym = DRV8830(
                ArgusV1Components.TORQUE_COILS_I2C,
                ArgusV1Components.TORQUE_YM_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                torque_ym = Middleware(torque_ym)

            self.__torque_ym_driver = torque_ym
            self.__device_list.append(torque_ym)
        except Exception as e:
            if self.__debug:
                raise e

            return [Errors.DRV8830_NOT_INITIALIZED]

        return [Errors.NOERROR]

    def __torque_z_boot(self) -> list[int]:
        """torque_z_boot: Boot sequence for the torque driver in the z direction

        :return: Error code if the torque driver failed to initialize
        """
        try:
            torque_z = DRV8830(
                ArgusV1Components.TORQUE_COILS_I2C,
                ArgusV1Components.TORQUE_Z_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                torque_z = Middleware(torque_z)

            self.__torque_z_driver = torque_z
            self.__device_list.append(torque_z)
        except Exception as e:
            if self.__debug:
                raise e

            return [Errors.DRV8830_NOT_INITIALIZED]

        return [Errors.NOERROR]

    def __torque_interface_boot(self) -> list[int]:
        """torque_interface_boot: Boot sequence for the torque interface

        :return: Error code if the torque interface failed to initialize
        """
        error_list: list[int] = []

        error_list += self.__torque_xp_boot()
        error_list += self.__torque_xm_boot()
        error_list += self.__torque_yp_boot()
        error_list += self.__torque_ym_boot()
        error_list += self.__torque_z_boot()

        # X direction
        try:
            torque_interface = TorqueInterface(self.__torque_xp_driver, self.__torque_xm_driver)
            self.__torque_x = torque_interface
        except Exception as e:
            if self.__debug:
                raise e

        # Y direction
        try:
            torque_interface = TorqueInterface(self.__torque_yp_driver, self.__torque_ym_driver)
            self.__torque_y = torque_interface
        except Exception as e:
            if self.__debug:
                raise e

        # Z direction
        try:
            torque_interface = TorqueInterface(self.__torque_z_driver)
            self.__torque_z = torque_interface
        except Exception as e:
            if self.__debug:
                raise e

        return error_list

    def __light_sensor_xp_boot(self) -> list[int]:
        """light_sensor_xp_boot: Boot sequence for the light sensor in the x+ direction

        :return: Error code if the light sensor failed to initialize
        """
        try:
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

            return [Errors.OPT4001_NOT_INITIALIZED]

        return [Errors.NOERROR]

    def __light_sensor_xm_boot(self) -> list[int]:
        """light_sensor_xm_boot: Boot sequence for the light sensor in the x- direction

        :return: Error code if the light sensor failed to initialize
        """
        try:
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

            return [Errors.OPT4001_NOT_INITIALIZED]

        return [Errors.NOERROR]

    def __light_sensor_yp_boot(self) -> list[int]:
        """light_sensor_yp_boot: Boot sequence for the light sensor in the y+ direction

        :return: Error code if the light sensor failed to initialize
        """
        try:
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

            return [Errors.OPT4001_NOT_INITIALIZED]

        return [Errors.NOERROR]

    def __light_sensor_ym_boot(self) -> list[int]:
        """light_sensor_ym_boot: Boot sequence for the light sensor in the y- direction

        :return: Error code if the light sensor failed to initialize
        """
        try:
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

            return [Errors.OPT4001_NOT_INITIALIZED]

        return [Errors.NOERROR]

    def __light_sensor_zm_boot(self) -> list[int]:
        """light_sensor_zm_boot: Boot sequence for the light sensor in the z+ direction

        :return: Error code if the light sensor failed to initialize
        """
        try:
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

            return [Errors.OPT4001_NOT_INITIALIZED]

        return [Errors.NOERROR]

    def __radio_boot(self) -> list[int]:
        """radio_boot: Boot sequence for the radio

        :return: Error code if the radio failed to initialize
        """
        try:
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

            return [Errors.RFM9X_NOT_INITIALIZED]

        return [Errors.NOERROR]

    def __rtc_boot(self) -> list[int]:
        """rtc_boot: Boot sequence for the RTC

        :return: Error code if the RTC failed to initialize
        """
        try:
            rtc = PCF8523(ArgusV1Components.RTC_I2C, ArgusV1Components.RTC_I2C_ADDRESS)

            if self.__middleware_enabled:
                rtc = Middleware(rtc)

            self.__rtc = rtc
            self.__device_list.append(rtc)
        except Exception as e:
            if self.__debug:
                raise e

            return [Errors.PCF8523_NOT_INITIALIZED]

        return [Errors.NOERROR]

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

            return [Errors.NEOPIXEL_NOT_INITIALIZED]

        return [Errors.NOERROR]

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

            return [Errors.SDCARD_NOT_INITIALIZED]

        return [Errors.NOERROR]

    def __vfs_boot(self) -> list[int]:
        """vfs_boot: Boot sequence for the VFS"""
        if self.__sd_card is None:
            return [Errors.SDCARD_NOT_INITIALIZED]

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

            return [Errors.VFS_NOT_INITIALIZED]

        return [Errors.NOERROR]

    def __burn_wire_boot(self) -> list[int]:
        """burn_wire_boot: Boot sequence for the burn wires"""
        try:
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

            return [Errors.BURNWIRES_NOT_INITIALIZED]

        return [Errors.NOERROR]

    def __payload_uart_boot(self) -> list[int]:
        """payload_uart_boot: Boot sequence for the Jetson UART"""
        try:
            payload_uart = PayloadUART(
                ArgusV1Components.PAYLOAD_UART,
                ArgusV1Components.PAYLOAD_ENABLE,
            )

            if self.__middleware_enabled:
                payload_uart = Middleware(payload_uart)

            self.__payload_uart = payload_uart
            self.__device_list.append(self.__payload_uart)
        except Exception as e:
            if self.__debug:
                raise e

            return [Errors.PAYLOAD_UART_NOT_INITIALIZED]

        return [Errors.NOERROR]

    ######################## DIAGNOSTICS ########################
    def __get_device_diagnostic_error(self, device) -> list[int]:  # noqa: C901
        """__get_device_diagnostic_error: Get the error code for a device that failed to initialize"""
        if isinstance(device, Middleware):  # Convert device to the wrapped instance
            device = device.get_instance()

        if device is self.RTC:
            return Errors.DIAGNOSTICS_ERROR_RTC
        elif device is self.GPS:
            return Errors.DIAGNOSTICS_ERROR_GPS
        elif device is self.BATTERY_POWER_MONITOR:
            return Errors.DIAGNOSTICS_ERROR_BATTERY_POWER_MONITOR
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
