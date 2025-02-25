"""
Author: Harry, Thomas, Ibrahima, Perrin
Description: This file contains the definition of the ArgusV3 class and its associated interfaces and components.
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


class ArgusV3Interfaces:
    """
    This class represents the interfaces used in the ArgusV3 module.
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

    # JET_SPI_SCK = board.CLK1  # GPIO10
    # JET_SPI_MOSI = board.MOSI1  # GPIO11
    # JET_SPI_MISO = board.MISO1  # GPIO08
    # JET_SPI = SPI(JET_SPI_SCK, MOSI=JET_SPI_MOSI, MISO=JET_SPI_MISO)

    SPI_SCK = board.CLK0  # GPIO18
    SPI_MOSI = board.MOSI0  # GPIO19
    SPI_MISO = board.MISO0  # GPIO16
    SPI = SPI(SPI_SCK, MOSI=SPI_MOSI, MISO=SPI_MISO)

    # UART0_BAUD = const(115200)
    # UART0_TX = board.TX0  # GPIO12
    # UART0_RX = board.RX0  # GPIO13
    # UART0 = UART(UART0_TX, UART0_RX, baudrate=UART0_BAUD)

    # UART1_BAUD = const(115200)
    # UART1_TX = board.TX1  # GPIO4
    # UART1_RX = board.RX1  # GPIO5
    # UART1 = UART(UART1_TX, UART1_RX, baudrate=UART1_BAUD)


class ArgusV3Components:
    """
    Represents the components used in the Argus V3 system.

    This class defines constants for various components such as GPS, battery,
    power monitor, Jetson power monitor, IMU, charger, torque coils,
    light sensors, radio, and SD card.
    """

    ########
    # I2C0 #
    ########

    # RTC
    RTC_I2C = ArgusV3Interfaces.I2C0
    RTC_I2C_ADDRESS = const(0x68)

    # IMU
    IMU_I2C = ArgusV3Interfaces.I2C0
    IMU_I2C_ADDRESS = const(0x4A)

    # BATTERY BOARD FUEL GAUGE
    FUEL_GAUGE_I2C = ArgusV3Interfaces.I2C0
    FUEL_GAUGE_I2C_ADDRESS = const(0x36)

    # JETSON POWER MONITOR
    JETSON_POWER_MONITOR_I2C = ArgusV3Interfaces.I2C0
    JETSON_POWER_MONITOR_I2C_ADDRESS = const(0x45)  # 8A

    # XM TORQUE COILS
    TORQUE_COILS_XM_I2C = ArgusV3Interfaces.I2C0
    TORQUE_XM_I2C_ADDRESS = const(0x64)

    # XM COIL DRIVER POWER MONITOR
    TORQUE_XM_POWER_MONITOR_I2C = ArgusV3Interfaces.I2C0
    TORQUE_XM_POWER_MONITOR_I2C_ADDRESS = const(0x40)  # 80

    # XM SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_XM_POWER_MONITOR_I2C = ArgusV3Interfaces.I2C0
    SOLAR_CHARGING_XM_POWER_MONITOR_I2C_ADDRESS = const(0x48)  # 90

    # XM LIGHT SENSOR
    LIGHT_SENSOR_XM_I2C = ArgusV3Interfaces.I2C0
    LIGHT_SENSOR_XM_I2C_ADDRESS = const(0x45)

    # YM TORQUE COILS
    TORQUE_COILS_YM_I2C = ArgusV3Interfaces.I2C0
    TORQUE_YM_I2C_ADDRESS = const(0x63)

    # Y COIL DRIVER POWER MONITOR
    TORQUE_YM_POWER_MONITOR_I2C = ArgusV3Interfaces.I2C0
    TORQUE_YM_POWER_MONITOR_I2C_ADDRESS = const(0x42)  # 80

    # Y SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_YM_POWER_MONITOR_I2C = ArgusV3Interfaces.I2C0
    SOLAR_CHARGING_YM_POWER_MONITOR_I2C_ADDRESS = const(0x49)  # 90

    # Y LIGHT SENSOR
    LIGHT_SENSOR_YM_I2C = ArgusV3Interfaces.I2C0
    LIGHT_SENSOR_YM_I2C_ADDRESS = const(0x44)

    # Z TORQUE COILS
    TORQUE_COILS_ZP_I2C = ArgusV3Interfaces.I2C0
    TORQUE_ZP_I2C_ADDRESS = const(0x64)

    # Z COIL DRIVER POWER MONITOR
    TORQUE_ZP_POWER_MONITOR_I2C = ArgusV3Interfaces.I2C0
    TORQUE_ZP_POWER_MONITOR_I2C_ADDRESS = const(0x42)  # 84

    # ZP SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_ZP_POWER_MONITOR_I2C = ArgusV3Interfaces.I2C0
    SOLAR_CHARGING_ZP_POWER_MONITOR_I2C_ADDRESS = const(0x4A)  # 94

    # ZP SUN SENSOR
    SUN_SENSOR_ZP_I2C = ArgusV3Interfaces.I2C0
    SUN_SENSOR_ZP1_I2C_ADDRESS = const(0x44)  # Conflict with ZM
    SUN_SENSOR_ZP2_I2C_ADDRESS = const(0x45)
    SUN_SENSOR_ZP3_I2C_ADDRESS = const(0x46)
    SUN_SENSOR_ZP4_I2C_ADDRESS = const(0x47)

    ########
    # I2C1 #
    ########

    # LORA POWER MONITOR
    RADIO_POWER_MONITOR_I2C = ArgusV3Interfaces.I2C1
    RADIO_POWER_MONITOR_I2C_ADDRESS = const(0x41)

    # USB CHARGER
    CHARGER_I2C = ArgusV3Interfaces.I2C1
    CHARGER_I2C_ADDRESS = const(0x6B)

    # GPS POWER MONITOR
    GPS_POWER_MONITOR_I2C = ArgusV3Interfaces.I2C1
    GPS_POWER_MONITOR_I2C_ADDRESS = const(0x42)

    # BOARD POWER MONITOR
    BOARD_POWER_MONITOR_I2C = ArgusV3Interfaces.I2C1
    BOARD_POWER_MONITOR_I2C_ADDRESS = const(0x40)

    # CAMERA

    # X TORQUE COILS
    TORQUE_COILS_XP_I2C = ArgusV3Interfaces.I2C1
    TORQUE_XP_I2C_ADDRESS = const(0x64)

    # X COIL DRIVER POWER MONITOR
    TORQUE_XP_POWER_MONITOR_I2C = ArgusV3Interfaces.I2C1
    TORQUE_XP_POWER_MONITOR_I2C_ADDRESS = const(0x42)  # 84

    # X SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_XP_POWER_MONITOR_I2C = ArgusV3Interfaces.I2C1
    SOLAR_CHARGING_XP_POWER_MONITOR_I2C_ADDRESS = const(0x49)  # 92

    # X LIGHT SENSOR
    LIGHT_SENSOR_XP_I2C = ArgusV3Interfaces.I2C1
    LIGHT_SENSOR_XP_I2C_ADDRESS = const(0x45)

    # Y TORQUE COILS
    TORQUE_COILS_YP_I2C = ArgusV3Interfaces.I2C1
    TORQUE_YP_I2C_ADDRESS = const(0x64)

    # Y COIL DRIVER POWER MONITOR
    TORQUE_YP_POWER_MONITOR_I2C = ArgusV3Interfaces.I2C1
    TORQUE_YP_POWER_MONITOR_I2C_ADDRESS = const(0x42)  # 84

    # Y SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_YP_POWER_MONITOR_I2C = ArgusV3Interfaces.I2C1
    SOLAR_CHARGING_YP_POWER_MONITOR_I2C_ADDRESS = const(0x49)  # 92

    # Y LIGHT SENSOR
    LIGHT_SENSOR_YP_I2C = ArgusV3Interfaces.I2C1
    LIGHT_SENSOR_YP_I2C_ADDRESS = const(0x45)

    # Z TORQUE COILS
    TORQUE_COILS_ZM_I2C = ArgusV3Interfaces.I2C1
    TORQUE_ZM_I2C_ADDRESS = const(0x63)

    # Z COIL DRIVER POWER MONITOR
    TORQUE_ZM_POWER_MONITOR_I2C = ArgusV3Interfaces.I2C1
    TORQUE_ZM_POWER_MONITOR_I2C_ADDRESS = const(0x40)  # 80

    # ZM LIGHT SENSOR
    LIGHT_SENSOR_ZM_I2C = ArgusV3Interfaces.I2C1
    LIGHT_SENSOR_ZM_I2C_ADDRESS = const(0x44)  # Conflict with ZP

    ########
    # SPI0 #
    ########

    # SD CARD
    SD_CARD_SPI = ArgusV3Interfaces.SPI
    SD_CARD_CS = board.SD_CS  # GPIO26_ADC0
    SD_BAUD = const(4000000)  # 4 MHz

    # RADIO
    # RADIO_SPI = ArgusV3Interfaces.SPI
    # RADIO_CS = board.LORA_CS  # GPIO17
    # RADIO_RESET = board.LORA_nRST  # GPIO21
    # RADIO_ENABLE = board.LORA_EN  # GPIO28_ADC2
    # RADIO_TX_EN = board.LORA_TX_EN  # GPIO22
    # RADIO_RX_EN = board.LORA_RX_EN  # GPIO20
    # RADIO_BUSY = board.LORA_BUSY  # GPIO23
    # RADIO_IRQ = board.GPS_EN  # GPIO27_ADC1
    # RADIO_FREQ = 915.6

    ########
    # SPI1 #
    ########

    # PAYLOAD(JETSON)
    # PAYLOAD_SPI = ArgusV3Interfaces.JET_SPI
    # PAYLOAD_CS = board.JETSON_CS  # GPIO9
    # PAYLOAD_ENABLE = board.JETSON_EN  # GPIO24

    #########
    # UART0 #
    #########

    # GPS
    # GPS_UART = ArgusV3Interfaces.UART0
    # GPS_ENABLE = board.GPS_EN  # GPIO27_ADC1

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


class ArgusV3(CubeSat):
    """ArgusV3: Represents the Argus V2 CubeSat."""

    def __init__(self, debug: bool = False):
        """__init__: Initializes the Argus V2 CubeSat."""
        self.__debug = debug

        super().__init__()

    ######################## BOOT SEQUENCE ########################

    def boot_sequence(self):
        """boot_sequence: Boot sequence for the CubeSat."""

        for name, device in self.__device_list.items():
            func = device.boot_fn
            device.device, device.error = func(name)

        # self.__recent_errors = error_list

        # return error_list

    def __state_flags_boot(self) -> None:
        """state_flags_boot: Boot sequence for the state flags"""
        from hal.drivers.stateflags import StateFlags

        self.__state_flags = StateFlags()

    def __gps_boot(self, _) -> list[object, int]:
        """GPS_boot: Boot sequence for the GPS

        :return: Error code if the GPS failed to initialize
        """

        from hal.drivers.gps import GPS

        try:
            gps = GPS(ArgusV3Components.GPS_UART, ArgusV3Components.GPS_ENABLE)

            return [gps, Errors.NOERROR]
        except Exception as e:
            if self.__debug:
                raise e

            return [None, Errors.GPS_NOT_INITIALIZED]

    def __power_monitor_boot(self, location) -> list[object, int]:
        """power_monitor_boot: Boot sequence for the power monitor

        :return: Error code if the power monitor failed to initialize
        """

        from hal.drivers.adm1176 import ADM1176

        locations = {
            "BOARD_PWR": [ArgusV3Components.BOARD_POWER_MONITOR_I2C_ADDRESS, ArgusV3Components.BOARD_POWER_MONITOR_I2C],
            "RADIO_PWR": [ArgusV3Components.RADIO_POWER_MONITOR_I2C_ADDRESS, ArgusV3Components.RADIO_POWER_MONITOR_I2C],
            "GPS_PWR": [ArgusV3Components.GPS_POWER_MONITOR_I2C_ADDRESS, ArgusV3Components.GPS_POWER_MONITOR_I2C],
            "JETSON_PWR": [ArgusV3Components.JETSON_POWER_MONITOR_I2C_ADDRESS, ArgusV3Components.JETSON_POWER_MONITOR_I2C],
            "TORQUE_XP_PWR": [
                ArgusV3Components.TORQUE_XP_POWER_MONITOR_I2C_ADDRESS,
                ArgusV3Components.TORQUE_XP_POWER_MONITOR_I2C,
            ],
            "TORQUE_XM_PWR": [
                ArgusV3Components.TORQUE_XM_POWER_MONITOR_I2C_ADDRESS,
                ArgusV3Components.TORQUE_XM_POWER_MONITOR_I2C,
            ],
            "TORQUE_YP_PWR": [
                ArgusV3Components.TORQUE_YP_POWER_MONITOR_I2C_ADDRESS,
                ArgusV3Components.TORQUE_YP_POWER_MONITOR_I2C,
            ],
            "TORQUE_YM_PWR": [
                ArgusV3Components.TORQUE_YM_POWER_MONITOR_I2C_ADDRESS,
                ArgusV3Components.TORQUE_YM_POWER_MONITOR_I2C,
            ],
            "TORQUE_ZP_PWR": [
                ArgusV3Components.TORQUE_ZP_POWER_MONITOR_I2C_ADDRESS,
                ArgusV3Components.TORQUE_ZP_POWER_MONITOR_I2C,
            ],
            "TORQUE_ZM_PWR": [
                ArgusV3Components.TORQUE_ZM_POWER_MONITOR_I2C_ADDRESS,
                ArgusV3Components.TORQUE_ZM_POWER_MONITOR_I2C,
            ],
            "SOLAR_XP_PWR": [
                ArgusV3Components.SOLAR_CHARGING_XP_POWER_MONITOR_I2C_ADDRESS,
                ArgusV3Components.SOLAR_CHARGING_XP_POWER_MONITOR_I2C,
            ],
            "SOLAR_XM_PWR": [
                ArgusV3Components.SOLAR_CHARGING_XM_POWER_MONITOR_I2C_ADDRESS,
                ArgusV3Components.SOLAR_CHARGING_XM_POWER_MONITOR_I2C,
            ],
            "SOLAR_YP_PWR": [
                ArgusV3Components.SOLAR_CHARGING_YP_POWER_MONITOR_I2C_ADDRESS,
                ArgusV3Components.SOLAR_CHARGING_YP_POWER_MONITOR_I2C,
            ],
            "SOLAR_YM_PWR": [
                ArgusV3Components.SOLAR_CHARGING_YM_POWER_MONITOR_I2C_ADDRESS,
                ArgusV3Components.SOLAR_CHARGING_YM_POWER_MONITOR_I2C,
            ],
            "SOLAR_ZP_PWR": [
                ArgusV3Components.SOLAR_CHARGING_ZP_POWER_MONITOR_I2C_ADDRESS,
                ArgusV3Components.SOLAR_CHARGING_ZP_POWER_MONITOR_I2C,
            ],
        }
        data = locations[location]
        try:
            address = data[0]
            bus = data[1]
            power_monitor = ADM1176(bus, address)

            return [power_monitor, Errors.NOERROR]

        except Exception as e:
            print(f"Failed to initialize {location}: {e}")
            if self.__debug:
                raise e
            return [None, Errors.ADM1176_NOT_INITIALIZED]

    def __imu_boot(self, _) -> list[object, int]:
        """imu_boot: Boot sequence for the IMU

        :return: Error code if the IMU failed to initialize
        """

        from hal.drivers.bno085 import BNO085, BNO_REPORT_UNCAL_GYROSCOPE, BNO_REPORT_UNCAL_MAGNETOMETER

        try:
            imu = BNO085(
                ArgusV3Components.IMU_I2C,
                ArgusV3Components.IMU_I2C_ADDRESS,
            )
            imu.enable_feature(BNO_REPORT_UNCAL_MAGNETOMETER)
            imu.enable_feature(BNO_REPORT_UNCAL_GYROSCOPE)

            return [imu, Errors.NOERROR]
        except Exception as e:
            print(f"Failed to initialize IMU: {e}")
            if self.__debug:
                raise e
            return [None, Errors.IMU_NOT_INITIALIZED]

    def __torque_drivers_boot(self, direction) -> list[int]:
        """Boot sequence for all torque drivers in predefined directions.

        :return: List of error codes for each torque driver in the order of directions
        """
        directions = {
            "XP": [ArgusV3Components.TORQUE_XP_I2C_ADDRESS, ArgusV3Components.TORQUE_COILS_XP_I2C],
            "XM": [ArgusV3Components.TORQUE_XM_I2C_ADDRESS, ArgusV3Components.TORQUE_COILS_XM_I2C],
            "YP": [ArgusV3Components.TORQUE_YP_I2C_ADDRESS, ArgusV3Components.TORQUE_COILS_YP_I2C],
            "YM": [ArgusV3Components.TORQUE_YM_I2C_ADDRESS, ArgusV3Components.TORQUE_COILS_YM_I2C],
            "ZP": [ArgusV3Components.TORQUE_ZP_I2C_ADDRESS, ArgusV3Components.TORQUE_COILS_ZP_I2C],
            "ZM": [ArgusV3Components.TORQUE_ZM_I2C_ADDRESS, ArgusV3Components.TORQUE_COILS_ZM_I2C],
        }

        from hal.drivers.drv8830 import DRV8830

        data = directions[direction]

        try:
            address = data[0]
            bus = data[1]
            torque_driver = DRV8830(bus, address)

            return [torque_driver, Errors.NOERROR]

        except Exception as e:
            if self.__debug:
                print(f"Failed to initialize {direction} torque driver: {e}")
                raise e
            return [None, Errors.DRV8830_NOT_INITIALIZED]  # Append failure code

    def __light_sensors_boot(self, direction) -> list[object, int]:
        """Boot sequence for all light sensors in predefined directions.

        :return: List of error codes for each sensor in the order of directions
        """
        directions = {
            "XP": [ArgusV3Components.LIGHT_SENSOR_XP_I2C_ADDRESS, ArgusV3Components.LIGHT_SENSOR_XP_I2C],
            "XM": [ArgusV3Components.LIGHT_SENSOR_XM_I2C_ADDRESS, ArgusV3Components.LIGHT_SENSOR_XM_I2C],
            "YP": [ArgusV3Components.LIGHT_SENSOR_YP_I2C_ADDRESS, ArgusV3Components.LIGHT_SENSOR_YP_I2C],
            "YM": [ArgusV3Components.LIGHT_SENSOR_YM_I2C_ADDRESS, ArgusV3Components.LIGHT_SENSOR_YM_I2C],
            "ZM": [ArgusV3Components.LIGHT_SENSOR_ZM_I2C_ADDRESS, ArgusV3Components.LIGHT_SENSOR_ZM_I2C],
            "SUN1": [ArgusV3Components.SUN_SENSOR_ZP1_I2C_ADDRESS, ArgusV3Components.SUN_SENSOR_ZP_I2C],
            "SUN2": [ArgusV3Components.SUN_SENSOR_ZP2_I2C_ADDRESS, ArgusV3Components.SUN_SENSOR_ZP_I2C],
            "SUN3": [ArgusV3Components.SUN_SENSOR_ZP3_I2C_ADDRESS, ArgusV3Components.SUN_SENSOR_ZP_I2C],
            "SUN4": [ArgusV3Components.SUN_SENSOR_ZP4_I2C_ADDRESS, ArgusV3Components.SUN_SENSOR_ZP_I2C],
        }

        from hal.drivers.opt4001 import OPT4001

        data = directions[direction]

        try:
            address = data[0]
            bus = data[1]
            light_sensor = OPT4001(
                bus,
                address,
                conversion_time=ArgusV3Components.LIGHT_SENSOR_CONVERSION_TIME,
            )
            return [light_sensor, Errors.NOERROR]

        except Exception as e:
            if self.__debug:
                print(f"Failed to initialize {direction} light sensor: {e}")
                raise e
            return [None, Errors.OPT4001_NOT_INITIALIZED]  # Append failure code

    def __radio_boot(self, _) -> list[object, int]:
        """radio_boot: Boot sequence for the radio

        :return: Error code if the radio failed to initialize
        """

        from hal.drivers.sx126x import SX1262

        try:

            # Enable power to the radio
            radioEn = digitalio.DigitalInOut(ArgusV3Components.RADIO_ENABLE)
            radioEn.direction = digitalio.Direction.OUTPUT
            radioEn.value = True

            radio = SX1262(
                spi_bus=ArgusV3Interfaces.SPI,
                cs=ArgusV3Components.RADIO_CS,
                irq=ArgusV3Components.RADIO_IRQ,
                rst=ArgusV3Components.RADIO_RESET,
                gpio=ArgusV3Components.RADIO_BUSY,
                tx_en=ArgusV3Components.RADIO_TX_EN,
                rx_en=ArgusV3Components.RADIO_RX_EN,
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

            return [radio, Errors.NOERROR]

        except Exception as e:
            if self.__debug:
                raise e

            return [None, Errors.SX1262_NOT_INITIALIZED]

    def __rtc_boot(self, _) -> list[object, int]:
        """rtc_boot: Boot sequence for the RTC

        :return: Error code if the RTC failed to initialize
        """

        from hal.drivers.ds3231 import DS3231

        try:
            rtc = DS3231(ArgusV3Components.RTC_I2C, ArgusV3Components.RTC_I2C_ADDRESS)
            return [rtc, Errors.NOERROR]
        except Exception as e:
            if self.__debug:
                raise e

            return [None, Errors.PCF8523_NOT_INITIALIZED]

    def __sd_card_boot(self, _) -> list[object, int]:
        """sd_card_boot: Boot sequence for the SD card"""
        try:
            sd_card = SDCard(
                ArgusV3Components.SD_CARD_SPI,
                ArgusV3Components.SD_CARD_CS,
                ArgusV3Components.SD_BAUD,
            )

            vfs = VfsFat(sd_card)
            mount(vfs, ArgusV3Components.VFS_MOUNT_POINT)
            path.append(ArgusV3Components.VFS_MOUNT_POINT)
            return [vfs, Errors.NOERROR]
        except Exception as e:
            if self.__debug:
                raise e

            return [None, Errors.SDCARD_NOT_INITIALIZED]

    def __burn_wire_boot(self, _) -> list[object, int]:
        """burn_wire_boot: Boot sequence for the burn wires"""
        try:
            # TODO: Burnwire software module
            from hal.drivers.burnwire import BurnWires

            burn_wires = BurnWires(
                ArgusV3Components.BURN_WIRE_ENABLE,
                ArgusV3Components.BURN_WIRE_XP,
                ArgusV3Components.BURN_WIRE_XM,
                ArgusV3Components.BURN_WIRE_YP,
                ArgusV3Components.BURN_WIRE_YM,
            )

            return [burn_wires, Errors.NOERROR]
        except Exception as e:
            if self.__debug:
                raise e

            return [None, Errors.BURNWIRES_NOT_INITIALIZED]

    def __fuel_gauge_boot(self, _) -> list[object, int]:
        """fuel_gauge_boot: Boot sequence for the fuel gauge"""

        from hal.drivers.max17205 import MAX17205

        try:

            fuel_gauge = MAX17205(
                ArgusV3Components.FUEL_GAUGE_I2C,
                ArgusV3Components.FUEL_GAUGE_I2C_ADDRESS,
            )

            return [fuel_gauge, Errors.NOERROR]
        except Exception as e:
            if self.__debug:
                raise e
            return [None, Errors.MAX17205_NOT_INITIALIZED]

    def reboot_peripheral(self, device_name: str) -> int:
        """__reboot_peripheral: Reboot a peripheral

        :param peripheral: The peripheral to reboot
        :return: Error code if the reboot failed
        """
        if device_name not in self.__device_list:
            return Errors.PERIPHERAL_NOT_FOUND
        self.__device_list[device_name].device = None
        func = self.__device_list[device_name].boot_fn
        self.__device_list[device_name].device, self.__device_list[device_name].error = func(device_name)
        return self.__device_list[device_name].error
