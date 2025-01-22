"""
Author: Harry, Thomas, Ibrahima, Perrin
Description: This file contains the definition of the ArgusV2 class and its associated interfaces and components.
"""

from sys import path

import board
import digitalio
from busio import I2C, SPI, UART
from hal.cubesat import CubeSat
from hal.drivers.middleware.errors import Errors
from micropython import const
from sdcardio import SDCard
from storage import VfsFat, mount


class ArgusV2Interfaces:
    """
    This class represents the interfaces used in the ArgusV2 module.
    """

    I2C0_SDA = board.SDA0  # GPIO0
    I2C0_SCL = board.SCL0  # GPIO1

    # Line may not be connected, try except sequence
    try:
        I2C0 = I2C(I2C0_SCL, I2C0_SDA)
    except Exception:
        I2C0 = None

    I2C1_SDA = board.SDA1  # GPIO2
    I2C1_SCL = board.SCL1  # GPIO3

    # Line may not be connected, try except sequence
    try:
        I2C1 = I2C(I2C1_SCL, I2C1_SDA)
    except Exception:
        I2C1 = None

    JET_SPI_SCK = board.CLK1  # GPIO10
    JET_SPI_MOSI = board.MOSI1  # GPIO11
    JET_SPI_MISO = board.MISO1  # GPIO08
    JET_SPI = SPI(JET_SPI_SCK, MOSI=JET_SPI_MOSI, MISO=JET_SPI_MISO)

    SPI_SCK = board.CLK0  # GPIO18
    SPI_MOSI = board.MOSI0  # GPIO19
    SPI_MISO = board.MISO0  # GPIO16
    SPI = SPI(SPI_SCK, MOSI=SPI_MOSI, MISO=SPI_MISO)

    UART0_BAUD = const(9600)
    UART0_TX = board.TX0  # GPIO12
    UART0_RX = board.RX0  # GPIO13
    UART0 = UART(UART0_TX, UART0_RX, baudrate=UART0_BAUD)

    UART1_BAUD = const(9600)
    UART1_TX = board.TX1  # GPIO4
    UART1_RX = board.RX1  # GPIO5
    UART1 = UART(UART1_TX, UART1_RX, baudrate=UART1_BAUD)


class ArgusV2Components:
    """
    Represents the components used in the Argus V1 system.

    This class defines constants for various components such as GPS, battery,
    power monitor, Jetson power monitor, IMU, charger, torque coils,
    light sensors, radio, and SD card.
    """

    ########
    # I2C0 #
    ########

    # RTC
    RTC_I2C = ArgusV2Interfaces.I2C0
    RTC_I2C_ADDRESS = const(0x68)

    # IMU
    IMU_I2C = ArgusV2Interfaces.I2C0
    IMU_I2C_ADDRESS = const(0x4A)

    # BATTERY BOARD FUEL GAUGE
    FUEL_GAUGE_I2C = ArgusV2Interfaces.I2C0
    FUEL_GAUGE_I2C_ADDRESS = const(0x36)

    # JETSON POWER MONITOR
    JETSON_POWER_MONITOR_I2C = ArgusV2Interfaces.I2C0
    JETSON_POWER_MONITOR_I2C_ADDRESS = const(0x45)  # 8A

    # XM TORQUE COILS
    TORQUE_COILS_XM_I2C = ArgusV2Interfaces.I2C0
    TORQUE_XM_I2C_ADDRESS = const(0x63)

    # XM COIL DRIVER POWER MONITOR
    TORQUE_XM_POWER_MONITOR_I2C = ArgusV2Interfaces.I2C0
    TORQUE_XM_POWER_MONITOR_I2C_ADDRESS = const(0x40)  # 80

    # XM SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_XM_POWER_MONITOR_I2C = ArgusV2Interfaces.I2C0
    SOLAR_CHARGING_XM_POWER_MONITOR_I2C_ADDRESS = const(0x48)  # 90

    # XM LIGHT SENSOR
    LIGHT_SENSOR_XM_I2C = ArgusV2Interfaces.I2C0
    LIGHT_SENSOR_XM_I2C_ADDRESS = const(0x44)

    # YM TORQUE COILS
    TORQUE_COILS_YM_I2C = ArgusV2Interfaces.I2C0
    TORQUE_YM_I2C_ADDRESS = const(0x64)

    # Y COIL DRIVER POWER MONITOR
    TORQUE_YM_POWER_MONITOR_I2C = ArgusV2Interfaces.I2C0
    TORQUE_YM_POWER_MONITOR_I2C_ADDRESS = const(0x42)  # 80

    # Y SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_YM_POWER_MONITOR_I2C = ArgusV2Interfaces.I2C0
    SOLAR_CHARGING_YM_POWER_MONITOR_I2C_ADDRESS = const(0x49)  # 90

    # Y LIGHT SENSOR
    LIGHT_SENSOR_YM_I2C = ArgusV2Interfaces.I2C0
    LIGHT_SENSOR_YM_I2C_ADDRESS = const(0x45)

    # Z TORQUE COILS
    TORQUE_COILS_ZP_I2C = ArgusV2Interfaces.I2C0
    TORQUE_ZP_I2C_ADDRESS = const(0x64)

    # Z COIL DRIVER POWER MONITOR
    TORQUE_ZP_POWER_MONITOR_I2C = ArgusV2Interfaces.I2C0
    TORQUE_ZP_POWER_MONITOR_I2C_ADDRESS = const(0x42)  # 84

    # ZP SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_ZP_POWER_MONITOR_I2C = ArgusV2Interfaces.I2C0
    SOLAR_CHARGING_ZP_POWER_MONITOR_I2C_ADDRESS = const(0x4A)  # 94

    # ZP SUN SENSOR
    SUN_SENSOR_ZP_I2C = ArgusV2Interfaces.I2C0
    SUN_SENSOR_ZP1_I2C_ADDRESS = const(0x44)  # Conflict with ZM
    SUN_SENSOR_ZP2_I2C_ADDRESS = const(0x45)
    SUN_SENSOR_ZP3_I2C_ADDRESS = const(0x46)
    SUN_SENSOR_ZP4_I2C_ADDRESS = const(0x47)

    ########
    # I2C1 #
    ########

    # LORA POWER MONITOR
    RADIO_POWER_MONITOR_I2C = ArgusV2Interfaces.I2C1
    RADIO_POWER_MONITOR_I2C_ADDRESS = const(0x42)

    # USB CHARGER
    CHARGER_I2C = ArgusV2Interfaces.I2C1
    CHARGER_I2C_ADDRESS = const(0x6B)

    # GPS POWER MONITOR
    GPS_POWER_MONITOR_I2C = ArgusV2Interfaces.I2C1
    GPS_POWER_MONITOR_I2C_ADDRESS = const(0x40)

    # BOARD POWER MONITOR
    BOARD_POWER_MONITOR_I2C = ArgusV2Interfaces.I2C1
    BOARD_POWER_MONITOR_I2C_ADDRESS = const(0x48)

    # CAMERA

    # X TORQUE COILS
    TORQUE_COILS_XP_I2C = ArgusV2Interfaces.I2C1
    TORQUE_XP_I2C_ADDRESS = const(0x64)

    # X COIL DRIVER POWER MONITOR
    TORQUE_XP_POWER_MONITOR_I2C = ArgusV2Interfaces.I2C1
    TORQUE_XP_POWER_MONITOR_I2C_ADDRESS = const(0x42)  # 84

    # X SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_XP_POWER_MONITOR_I2C = ArgusV2Interfaces.I2C1
    SOLAR_CHARGING_XP_POWER_MONITOR_I2C_ADDRESS = const(0x49)  # 92

    # X LIGHT SENSOR
    LIGHT_SENSOR_XP_I2C = ArgusV2Interfaces.I2C1
    LIGHT_SENSOR_XP_I2C_ADDRESS = const(0x45)

    # Y TORQUE COILS
    TORQUE_COILS_YP_I2C = ArgusV2Interfaces.I2C1
    TORQUE_YP_I2C_ADDRESS = const(0x64)

    # Y COIL DRIVER POWER MONITOR
    TORQUE_YP_POWER_MONITOR_I2C = ArgusV2Interfaces.I2C1
    TORQUE_YP_POWER_MONITOR_I2C_ADDRESS = const(0x42)  # 84

    # Y SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_YP_POWER_MONITOR_I2C = ArgusV2Interfaces.I2C1
    SOLAR_CHARGING_YP_POWER_MONITOR_I2C_ADDRESS = const(0x49)  # 92

    # Y LIGHT SENSOR
    LIGHT_SENSOR_YP_I2C = ArgusV2Interfaces.I2C1
    LIGHT_SENSOR_YP_I2C_ADDRESS = const(0x45)

    # Z TORQUE COILS
    TORQUE_COILS_ZM_I2C = ArgusV2Interfaces.I2C1
    TORQUE_ZM_I2C_ADDRESS = const(0x63)

    # Z COIL DRIVER POWER MONITOR
    TORQUE_ZM_POWER_MONITOR_I2C = ArgusV2Interfaces.I2C1
    TORQUE_ZM_POWER_MONITOR_I2C_ADDRESS = const(0x40)  # 80

    # ZM LIGHT SENSOR
    LIGHT_SENSOR_ZM_I2C = ArgusV2Interfaces.I2C1
    LIGHT_SENSOR_ZM_I2C_ADDRESS = const(0x44)  # Conflict with ZP

    ########
    # SPI0 #
    ########

    # SD CARD
    SD_CARD_SPI = ArgusV2Interfaces.SPI
    SD_CARD_CS = board.SD_CS  # GPIO26_ADC0
    SD_BAUD = const(4000000)  # 4 MHz

    # RADIO
    RADIO_SPI = ArgusV2Interfaces.SPI
    RADIO_CS = board.LORA_CS  # GPIO17
    RADIO_RESET = board.LORA_nRST  # GPIO21
    RADIO_ENABLE = board.LORA_EN  # GPIO28_ADC2
    RADIO_TX_EN = board.LORA_TX_EN  # GPIO22
    RADIO_RX_EN = board.LORA_RX_EN  # GPIO20
    RADIO_BUSY = board.LORA_BUSY  # GPIO23
    RADIO_IRQ = board.GPS_EN  # GPIO27_ADC1
    # RADIO_FREQ = 915.6

    ########
    # SPI1 #
    ########

    # PAYLOAD(JETSON)
    PAYLOAD_SPI = ArgusV2Interfaces.JET_SPI
    PAYLOAD_CS = board.JETSON_CS  # GPIO9
    PAYLOAD_ENABLE = board.JETSON_EN  # GPIO24

    #########
    # UART0 #
    #########

    # GPS
    GPS_UART = ArgusV2Interfaces.UART0
    GPS_ENABLE = board.GPS_EN  # GPIO27_ADC1

    #########
    # UART1 #
    #########

    # RS485

    ########
    # OLD #
    ########

    # BURN WIRES
    # BURN_WIRE_ENABLE = board.RELAY_A
    # BURN_WIRE_XP = board.BURN1
    # BURN_WIRE_XM = board.BURN2
    # BURN_WIRE_YP = board.BURN3
    # BURN_WIRE_YM = board.BURN4

    # VFS
    VFS_MOUNT_POINT = "/sd"

    LIGHT_SENSOR_CONVERSION_TIME = 0b0000


class ArgusV2(CubeSat):
    """ArgusV2: Represents the Argus V2 CubeSat."""

    def __init__(self, debug: bool = False):
        """__init__: Initializes the Argus V2 CubeSat."""
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
        error_list.append(self.__radio_boot())
        error_list.append(self.__power_monitor_boot())
        error_list.append(self.__fuel_gauge_boot)
        error_list.append(self.__charger_boot())
        # error_list.append(self.__torque_drivers_boot())
        # error_list.append(self.__light_sensors_boot())  # light + sun sensors
        # error_list.append(self.__burn_wire_boot())

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

            gps1 = GPS(ArgusV2Components.GPS_UART, ArgusV2Components.GPS_ENABLE)

            self.__gps = gps1
            self.__device_list.append(gps1)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.GPS_NOT_INITIALIZED

        return Errors.NOERROR

    def __power_monitor_boot(self) -> list[int]:
        """power_monitor_boot: Boot sequence for the power monitor

        :return: Error code if the power monitor failed to initialize
        """

        locations = {
            "BOARD": [ArgusV2Components.BOARD_POWER_MONITOR_I2C_ADDRESS, ArgusV2Components.BOARD_POWER_MONITOR_I2C],
            "RADIO": [ArgusV2Components.RADIO_POWER_MONITOR_I2C_ADDRESS, ArgusV2Components.RADIO_POWER_MONITOR_I2C],
            # "GPS": [ArgusV2Components.GPS_POWER_MONITOR_I2C_ADDRESS, ArgusV2Components.GPS_POWER_MONITOR_I2C],
            # "JETSON": [ArgusV2Components.JETSON_POWER_MONITOR_I2C_ADDRESS, ArgusV2Components.JETSON_POWER_MONITOR_I2C],
            # "TORQUE_XP": [
            #     ArgusV2Components.TORQUE_XP_POWER_MONITOR_I2C_ADDRESS,
            #     ArgusV2Components.TORQUE_XP_POWER_MONITOR_I2C,
            # ],
            # "TORQUE_XM": [
            #     ArgusV2Components.TORQUE_XM_POWER_MONITOR_I2C_ADDRESS,
            #     ArgusV2Components.TORQUE_XM_POWER_MONITOR_I2C,
            # ],
            # "TORQUE_YP": [
            #     ArgusV2Components.TORQUE_YP_POWER_MONITOR_I2C_ADDRESS,
            #     ArgusV2Components.TORQUE_YP_POWER_MONITOR_I2C,
            # ],
            # "TORQUE_YM": [
            #     ArgusV2Components.TORQUE_YM_POWER_MONITOR_I2C_ADDRESS,
            #     ArgusV2Components.TORQUE_YM_POWER_MONITOR_I2C,
            # ],
            # "TORQUE_ZP": [
            #     ArgusV2Components.TORQUE_ZP_POWER_MONITOR_I2C_ADDRESS,
            #     ArgusV2Components.TORQUE_ZP_POWER_MONITOR_I2C,
            # ],
            # "TORQUE_ZM": [
            #     ArgusV2Components.TORQUE_ZM_POWER_MONITOR_I2C_ADDRESS,
            #     ArgusV2Components.TORQUE_ZM_POWER_MONITOR_I2C,
            # ],
            # "SOLAR_XP": [
            #     ArgusV2Components.SOLAR_CHARGING_XP_POWER_MONITOR_I2C_ADDRESS,
            #     ArgusV2Components.SOLAR_CHARGING_XP_POWER_MONITOR_I2C,
            # ],
            # "SOLAR_XM": [
            #     ArgusV2Components.SOLAR_CHARGING_XM_POWER_MONITOR_I2C_ADDRESS,
            #     ArgusV2Components.SOLAR_CHARGING_XM_POWER_MONITOR_I2C,
            # ],
            # "SOLAR_YP": [
            #     ArgusV2Components.SOLAR_CHARGING_YP_POWER_MONITOR_I2C_ADDRESS,
            #     ArgusV2Components.SOLAR_CHARGING_YP_POWER_MONITOR_I2C,
            # ],
            # "SOLAR_YM": [
            #     ArgusV2Components.SOLAR_CHARGING_YM_POWER_MONITOR_I2C_ADDRESS,
            #     ArgusV2Components.SOLAR_CHARGING_YM_POWER_MONITOR_I2C,
            # ],
            # "SOLAR_ZP": [
            #     ArgusV2Components.SOLAR_CHARGING_ZP_POWER_MONITOR_I2C_ADDRESS,
            #     ArgusV2Components.SOLAR_CHARGING_ZP_POWER_MONITOR_I2C,
            # ],
        }

        from hal.drivers.adm1176 import ADM1176

        error_codes = []

        for location, busAndAddress in locations.items():
            try:
                address = busAndAddress[0]
                bus = busAndAddress[1]
                power_monitor = ADM1176(bus, address)

                self.__power_monitors[location] = power_monitor
                self.__device_list.append(power_monitor)
                error_codes.append(Errors.NOERROR)  # Append success code if no error
            except Exception as e:
                self.__power_monitors[location] = None
                if self.__debug:
                    print(f"Failed to initialize {location} power driver: {e}")
                    raise e
                return Errors.ADM1176_NOT_INITIALIZED

        return error_codes

    def __imu_boot(self) -> list[int]:
        """imu_boot: Boot sequence for the IMU

        :return: Error code if the IMU failed to initialize
        """
        try:
            # from hal.drivers.bno08x_i2c import BNO08X_I2C
            # TODO: Modify HAL for getting raw values from the IMU
            from hal.drivers.bno085 import BNO085, BNO_REPORT_UNCAL_GYROSCOPE, BNO_REPORT_UNCAL_MAGNETOMETER

            imu = BNO085(ArgusV2Components.IMU_I2C, ArgusV2Components.IMU_I2C_ADDRESS)
            imu.enable_feature(BNO_REPORT_UNCAL_MAGNETOMETER)
            imu.enable_feature(BNO_REPORT_UNCAL_GYROSCOPE)

            self.__imu = imu
            self.__imu_temp_flag = False
            self.__device_list.append(imu)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.IMU_NOT_INITIALIZED

        return Errors.NOERROR

    def __charger_boot(self) -> list[int]:
        """charger_boot: Boot sequence for the charger

        :return: Error code if the charger failed to initialize
        """
        try:
            from hal.drivers.bq25883 import BQ25883

            charger = BQ25883(
                ArgusV2Components.CHARGER_I2C,
                ArgusV2Components.CHARGER_I2C_ADDRESS,
            )

            self.__charger = charger
            self.__device_list.append(charger)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.BQ25883_NOT_INITIALIZED

        return Errors.NOERROR

    def __torque_drivers_boot(self) -> list[int]:
        """Boot sequence for all torque drivers in predefined directions.

        :return: List of error codes for each torque driver in the order of directions
        """
        directions = {
            "XP": [ArgusV2Components.TORQUE_XP_I2C_ADDRESS, ArgusV2Components.TORQUE_COILS_XP_I2C],
            "XM": [ArgusV2Components.TORQUE_XM_I2C_ADDRESS, ArgusV2Components.TORQUE_COILS_XM_I2C],
            "YP": [ArgusV2Components.TORQUE_YP_I2C_ADDRESS, ArgusV2Components.TORQUE_COILS_YP_I2C],
            "YM": [ArgusV2Components.TORQUE_YM_I2C_ADDRESS, ArgusV2Components.TORQUE_COILS_YM_I2C],
            "ZP": [ArgusV2Components.TORQUE_ZP_I2C_ADDRESS, ArgusV2Components.TORQUE_COILS_ZP_I2C],
            "ZM": [ArgusV2Components.TORQUE_ZM_I2C_ADDRESS, ArgusV2Components.TORQUE_COILS_ZM_I2C],
        }

        from hal.drivers.drv8830 import DRV8830

        error_codes = []

        for direction, busAndAddress in directions.items():
            try:
                address = busAndAddress[0]
                bus = busAndAddress[1]
                torque_driver = DRV8830(bus, address)

                self.__torque_drivers[direction] = torque_driver
                self.__device_list.append(torque_driver)
                error_codes.append(Errors.NOERROR)  # Append success code if no error

            except Exception as e:
                self.__torque_drivers[direction] = None
                if self.__debug:
                    print(f"Failed to initialize {direction} torque driver: {e}")
                    raise e
                error_codes.append(Errors.DRV8830_NOT_INITIALIZED)  # Append failure code

        return error_codes

    def __light_sensors_boot(self) -> list[int]:
        """Boot sequence for all light sensors in predefined directions.

        :return: List of error codes for each sensor in the order of directions
        """
        directions = {
            "XP": [ArgusV2Components.LIGHT_SENSOR_XP_I2C_ADDRESS, ArgusV2Components.LIGHT_SENSOR_XP_I2C],
            "XM": [ArgusV2Components.LIGHT_SENSOR_XM_I2C_ADDRESS, ArgusV2Components.LIGHT_SENSOR_XM_I2C],
            "YP": [ArgusV2Components.LIGHT_SENSOR_YP_I2C_ADDRESS, ArgusV2Components.LIGHT_SENSOR_YP_I2C],
            "YM": [ArgusV2Components.LIGHT_SENSOR_YM_I2C_ADDRESS, ArgusV2Components.LIGHT_SENSOR_YM_I2C],
            "ZM": [ArgusV2Components.LIGHT_SENSOR_ZM_I2C_ADDRESS, ArgusV2Components.LIGHT_SENSOR_ZM_I2C],
            "ZP1": [ArgusV2Components.SUN_SENSOR_ZP1_I2C_ADDRESS, ArgusV2Components.SUN_SENSOR_ZP_I2C],
            "ZP2": [ArgusV2Components.SUN_SENSOR_ZP2_I2C_ADDRESS, ArgusV2Components.SUN_SENSOR_ZP_I2C],
            "ZP3": [ArgusV2Components.SUN_SENSOR_ZP3_I2C_ADDRESS, ArgusV2Components.SUN_SENSOR_ZP_I2C],
            "ZP4": [ArgusV2Components.SUN_SENSOR_ZP4_I2C_ADDRESS, ArgusV2Components.SUN_SENSOR_ZP_I2C],
        }

        from hal.drivers.opt4001 import OPT4001

        error_codes = []  # List to store error codes per sensor

        for direction, busAndAddress in directions.items():
            try:
                address = busAndAddress[0]
                bus = busAndAddress[1]
                light_sensor = OPT4001(
                    bus,
                    address,
                    conversion_time=ArgusV2Components.LIGHT_SENSOR_CONVERSION_TIME,
                )

                self.__light_sensors[direction] = light_sensor
                self.__device_list.append(light_sensor)
                error_codes.append(Errors.NOERROR)  # Append success code if no error

            except Exception as e:
                self.__light_sensors[direction] = None
                if self.__debug:
                    print(f"Failed to initialize {direction} light sensor: {e}")
                    raise e
                error_codes.append(Errors.OPT4001_NOT_INITIALIZED)  # Append failure code

        return error_codes

    def __radio_boot(self) -> list[int]:
        """radio_boot: Boot sequence for the radio

        :return: Error code if the radio failed to initialize
        """
        try:
            from hal.drivers.sx126x import SX1262

            # Enable power to the radio
            radioEn = digitalio.DigitalInOut(ArgusV2Components.RADIO_ENABLE)
            radioEn.direction = digitalio.Direction.OUTPUT
            radioEn.value = True

            radio = SX1262(
                spi_bus=ArgusV2Interfaces.SPI,
                cs=ArgusV2Components.RADIO_CS,
                irq=ArgusV2Components.RADIO_IRQ,
                rst=ArgusV2Components.RADIO_RESET,
                gpio=ArgusV2Components.RADIO_BUSY,
                tx_en=ArgusV2Components.RADIO_TX_EN,
                rx_en=ArgusV2Components.RADIO_RX_EN,
            )

            radio.begin(
                freq=915.6,
                bw=125,
                sf=7,
                cr=8,
                syncWord=0x12,
                power=22,
                currentLimit=140.0,
                preambleLength=8,
                implicit=False,
                implicitLen=0xFF,
                crcOn=True,
                txIq=False,
                rxIq=False,
                tcxoVoltage=1.7,
                useRegulatorLDO=False,
                blocking=True,
            )

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
            from hal.drivers.ds3231 import DS3231

            rtc = DS3231(ArgusV2Components.RTC_I2C, ArgusV2Components.RTC_I2C_ADDRESS)

            self.__rtc = rtc
            self.__device_list.append(rtc)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.PCF8523_NOT_INITIALIZED

        return Errors.NOERROR

    def __sd_card_boot(self) -> list[int]:
        """sd_card_boot: Boot sequence for the SD card"""
        try:
            sd_card = SDCard(
                ArgusV2Components.SD_CARD_SPI,
                ArgusV2Components.SD_CARD_CS,
                ArgusV2Components.SD_BAUD,
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

            mount(vfs, ArgusV2Components.VFS_MOUNT_POINT)
            path.append(ArgusV2Components.VFS_MOUNT_POINT)

            path.append(ArgusV2Components.VFS_MOUNT_POINT)
            self.__vfs = vfs
        except Exception as e:
            if self.__debug:
                raise e
            return Errors.VFS_NOT_INITIALIZED

        return Errors.NOERROR

    def __burn_wire_boot(self) -> list[int]:
        """burn_wire_boot: Boot sequence for the burn wires"""
        try:
            from hal.drivers.burnwire import BurnWires

            burn_wires = BurnWires(
                ArgusV2Components.BURN_WIRE_ENABLE,
                ArgusV2Components.BURN_WIRE_XP,
                ArgusV2Components.BURN_WIRE_XM,
                ArgusV2Components.BURN_WIRE_YP,
                ArgusV2Components.BURN_WIRE_YM,
            )

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
                ArgusV2Components.FUEL_GAUGE_I2C
            )

            self.__fuel_gauge = fuel_gauge
            self.append_device(fuel_gauge)
        except Exception as e:
            if self.__debug:
                raise e

            return Errors.MAX17205_NOT_INITIALIZED

        return Errors.NOERROR
