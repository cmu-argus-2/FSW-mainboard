"""
Author: Ibrahima, Perrin
Description: This file contains the definition of the ArgusV2 class and its associated interfaces and components.
"""

from sys import path

import board
import digitalio
from busio import I2C, SPI, UART
from hal.cubesat import CubeSat
from hal.drivers.errors import Errors
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

    UART0_BAUD = const(115200)
    UART0_TX = board.TX0  # GPIO12
    UART0_RX = board.RX0  # GPIO13
    UART0 = UART(UART0_TX, UART0_RX, baudrate=UART0_BAUD)

    UART1_BAUD = const(115200)
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
    TORQUE_XM_I2C_ADDRESS = const(0x30)

    # XM SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_XM_POWER_MONITOR_I2C = ArgusV2Interfaces.I2C0
    SOLAR_CHARGING_XM_POWER_MONITOR_I2C_ADDRESS = const(0x40)  # 90

    # XM LIGHT SENSOR
    LIGHT_SENSOR_XM_I2C = ArgusV2Interfaces.I2C0
    LIGHT_SENSOR_XM_I2C_ADDRESS = const(0x44)

    # YP TORQUE COILS
    TORQUE_COILS_YP_I2C = ArgusV2Interfaces.I2C0
    TORQUE_YP_I2C_ADDRESS = const(0x31)

    # YP SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_YP_POWER_MONITOR_I2C = ArgusV2Interfaces.I2C0
    SOLAR_CHARGING_YP_POWER_MONITOR_I2C_ADDRESS = const(0x41)  # 90

    # YP LIGHT SENSOR
    LIGHT_SENSOR_YP_I2C = ArgusV2Interfaces.I2C0
    LIGHT_SENSOR_YP_I2C_ADDRESS = const(0x45)

    # ZP TORQUE COILS
    TORQUE_COILS_ZP_I2C = ArgusV2Interfaces.I2C0
    TORQUE_ZP_I2C_ADDRESS = const(0x10)

    # ZP SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_ZP_POWER_MONITOR_I2C = ArgusV2Interfaces.I2C0
    SOLAR_CHARGING_ZP_POWER_MONITOR_I2C_ADDRESS = const(0x62)  # 94

    # ZP SUN SENSOR
    SUN_SENSOR_ZP_I2C = ArgusV2Interfaces.I2C0
    SUN_SENSOR_ZP1_I2C_ADDRESS = const(0x64)  # Conflict with ZM
    SUN_SENSOR_ZP2_I2C_ADDRESS = const(0x65)
    SUN_SENSOR_ZP3_I2C_ADDRESS = const(0x66)
    SUN_SENSOR_ZP4_I2C_ADDRESS = const(0x67)

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
    GPS_POWER_MONITOR_I2C_ADDRESS = const(0x41)

    # BOARD POWER MONITOR
    BOARD_POWER_MONITOR_I2C = ArgusV2Interfaces.I2C1
    BOARD_POWER_MONITOR_I2C_ADDRESS = const(0x40)

    # CAMERA

    # XP TORQUE COILS
    TORQUE_COILS_XP_I2C = ArgusV2Interfaces.I2C1
    TORQUE_XP_I2C_ADDRESS = const(0x30)

    # XP SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_XP_POWER_MONITOR_I2C = ArgusV2Interfaces.I2C1
    SOLAR_CHARGING_XP_POWER_MONITOR_I2C_ADDRESS = const(0x48)  # 92

    # XP LIGHT SENSOR
    LIGHT_SENSOR_XP_I2C = ArgusV2Interfaces.I2C1
    LIGHT_SENSOR_XP_I2C_ADDRESS = const(0x44)

    # YM TORQUE COILS
    TORQUE_COILS_YM_I2C = ArgusV2Interfaces.I2C1
    TORQUE_YM_I2C_ADDRESS = const(0x31)

    # YM SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_YM_POWER_MONITOR_I2C = ArgusV2Interfaces.I2C1
    SOLAR_CHARGING_YM_POWER_MONITOR_I2C_ADDRESS = const(0x4A)  # 92

    # YM LIGHT SENSOR
    LIGHT_SENSOR_YM_I2C = ArgusV2Interfaces.I2C1
    LIGHT_SENSOR_YM_I2C_ADDRESS = const(0x45)

    # ZM TORQUE COILS
    TORQUE_COILS_ZM_I2C = ArgusV2Interfaces.I2C1
    TORQUE_ZM_I2C_ADDRESS = const(0x32)

    # ZM LIGHT SENSOR
    LIGHT_SENSOR_ZM_I2C = ArgusV2Interfaces.I2C1
    LIGHT_SENSOR_ZM_I2C_ADDRESS = const(0x46)  # Conflict with ZP

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


class ArgusV2(CubeSat):
    """ArgusV2: Represents the Argus V2 CubeSat."""

    def __init__(self, debug: bool = False):
        """__init__: Initializes the Argus V2 CubeSat."""
        self.__debug = debug

        # v2 mainboards have no NEOPIXEL, and limited RAM
        # So, remove all components that do not exist on MB itself
        super().__init__()
        del self.__device_list["NEOPIXEL"]

        del self.__device_list["TORQUE_XP"]
        del self.__device_list["TORQUE_XM"]
        del self.__device_list["TORQUE_YP"]
        del self.__device_list["TORQUE_YM"]
        del self.__device_list["TORQUE_ZP"]
        del self.__device_list["TORQUE_ZM"]

        del self.__device_list["LIGHT_XP"]
        del self.__device_list["LIGHT_XM"]
        del self.__device_list["LIGHT_YP"]
        del self.__device_list["LIGHT_YM"]
        del self.__device_list["LIGHT_ZM"]

        del self.__device_list["XP_PWR"]
        del self.__device_list["XM_PWR"]
        del self.__device_list["YP_PWR"]
        del self.__device_list["YM_PWR"]
        del self.__device_list["ZP_PWR"]

    ######################## BOOT SEQUENCE ########################

    def boot_sequence(self):
        """boot_sequence: Boot sequence for the CubeSat."""

        for name, device in self.__device_list.items():
            func = device.boot_fn
            device.device, device.error = func(name)

    def __neopixel_boot(self, _) -> list[object, int]:
        """Mock for neopixel boot from ArgusV3"""
        pass

    def __gps_boot(self, _) -> list[object, int]:
        """GPS_boot: Boot sequence for the GPS

        :return: Error code if the GPS failed to initialize
        """

        from hal.drivers.gps import GPS

        try:
            gps = GPS(ArgusV2Components.GPS_UART, None, False, False)

            return [gps, Errors.NO_ERROR]
        except Exception as e:
            if self.__debug:
                raise e

            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __power_monitor_boot(self, location) -> list[object, int]:
        """power_monitor_boot: Boot sequence for the power monitor

        :return: Error code if the power monitor failed to initialize
        """

        from hal.drivers.adm1176 import ADM1176

        locations = {
            "BOARD_PWR": [ArgusV2Components.BOARD_POWER_MONITOR_I2C_ADDRESS, ArgusV2Components.BOARD_POWER_MONITOR_I2C],
            "RADIO_PWR": [ArgusV2Components.RADIO_POWER_MONITOR_I2C_ADDRESS, ArgusV2Components.RADIO_POWER_MONITOR_I2C],
            "GPS_PWR": [ArgusV2Components.GPS_POWER_MONITOR_I2C_ADDRESS, ArgusV2Components.GPS_POWER_MONITOR_I2C],
            "JETSON_PWR": [ArgusV2Components.JETSON_POWER_MONITOR_I2C_ADDRESS, ArgusV2Components.JETSON_POWER_MONITOR_I2C],
            "XP_PWR": [
                ArgusV2Components.SOLAR_CHARGING_XP_POWER_MONITOR_I2C_ADDRESS,
                ArgusV2Components.SOLAR_CHARGING_XP_POWER_MONITOR_I2C,
            ],
            "XM_PWR": [
                ArgusV2Components.SOLAR_CHARGING_XM_POWER_MONITOR_I2C_ADDRESS,
                ArgusV2Components.SOLAR_CHARGING_XM_POWER_MONITOR_I2C,
            ],
            "YP_PWR": [
                ArgusV2Components.SOLAR_CHARGING_YP_POWER_MONITOR_I2C_ADDRESS,
                ArgusV2Components.SOLAR_CHARGING_YP_POWER_MONITOR_I2C,
            ],
            "YM_PWR": [
                ArgusV2Components.SOLAR_CHARGING_YM_POWER_MONITOR_I2C_ADDRESS,
                ArgusV2Components.SOLAR_CHARGING_YM_POWER_MONITOR_I2C,
            ],
            "ZP_PWR": [
                ArgusV2Components.SOLAR_CHARGING_ZP_POWER_MONITOR_I2C_ADDRESS,
                ArgusV2Components.SOLAR_CHARGING_ZP_POWER_MONITOR_I2C,
            ],
        }
        data = locations[location]
        try:
            address = data[0]
            bus = data[1]
            power_monitor = ADM1176(bus, address)

            return [power_monitor, Errors.NO_ERROR]

        except Exception as e:
            if self.__debug:
                raise e
            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __imu_boot(self, _) -> list[object, int]:
        """imu_boot: Boot sequence for the IMU

        :return: Error code if the IMU failed to initialize
        """

        from hal.drivers.bno085 import BNO085, BNO_REPORT_UNCAL_GYROSCOPE, BNO_REPORT_UNCAL_MAGNETOMETER

        try:
            imu = BNO085(
                ArgusV2Components.IMU_I2C,
                ArgusV2Components.IMU_I2C_ADDRESS,
            )
            imu.enable_feature(BNO_REPORT_UNCAL_MAGNETOMETER)
            imu.enable_feature(BNO_REPORT_UNCAL_GYROSCOPE)

            return [imu, Errors.NO_ERROR]
        except Exception as e:
            if self.__debug:
                raise e
            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __torque_driver_boot(self, direction) -> list[int]:
        """Boot sequence for all torque drivers in predefined directions.

        :return: List of error codes for each torque driver in the order of directions
        """
        directions = {
            "TORQUE_XP": [ArgusV2Components.TORQUE_XP_I2C_ADDRESS, ArgusV2Components.TORQUE_COILS_XP_I2C],
            "TORQUE_XM": [ArgusV2Components.TORQUE_XM_I2C_ADDRESS, ArgusV2Components.TORQUE_COILS_XM_I2C],
            "TORQUE_YP": [ArgusV2Components.TORQUE_YP_I2C_ADDRESS, ArgusV2Components.TORQUE_COILS_YP_I2C],
            "TORQUE_YM": [ArgusV2Components.TORQUE_YM_I2C_ADDRESS, ArgusV2Components.TORQUE_COILS_YM_I2C],
            "TORQUE_ZP": [ArgusV2Components.TORQUE_ZP_I2C_ADDRESS, ArgusV2Components.TORQUE_COILS_ZP_I2C],
            "TORQUE_ZM": [ArgusV2Components.TORQUE_ZM_I2C_ADDRESS, ArgusV2Components.TORQUE_COILS_ZM_I2C],
        }
        # TODO: verify this driver actually works
        from hal.drivers.drv8235 import DRV8235

        data = directions[direction]

        try:
            address = data[0]
            bus = data[1]
            torque_driver = DRV8235(bus, address)

            return [torque_driver, Errors.NO_ERROR]

        except Exception as e:
            if self.__debug:
                raise e
            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __light_sensor_boot(self, direction) -> list[object, int]:
        """Boot sequence for all light sensors in predefined directions.

        :return: List of error codes for each sensor in the order of directions
        """
        directions = {
            "LIGHT_XP": [ArgusV2Components.LIGHT_SENSOR_XP_I2C_ADDRESS, ArgusV2Components.LIGHT_SENSOR_XP_I2C],
            "LIGHT_XM": [ArgusV2Components.LIGHT_SENSOR_XM_I2C_ADDRESS, ArgusV2Components.LIGHT_SENSOR_XM_I2C],
            "LIGHT_YP": [ArgusV2Components.LIGHT_SENSOR_YP_I2C_ADDRESS, ArgusV2Components.LIGHT_SENSOR_YP_I2C],
            "LIGHT_YM": [ArgusV2Components.LIGHT_SENSOR_YM_I2C_ADDRESS, ArgusV2Components.LIGHT_SENSOR_YM_I2C],
            "LIGHT_ZM": [ArgusV2Components.LIGHT_SENSOR_ZM_I2C_ADDRESS, ArgusV2Components.LIGHT_SENSOR_ZM_I2C],
            "LIGHT_ZP_1": [ArgusV2Components.SUN_SENSOR_ZP1_I2C_ADDRESS, ArgusV2Components.SUN_SENSOR_ZP_I2C],
            "LIGHT_ZP_2": [ArgusV2Components.SUN_SENSOR_ZP2_I2C_ADDRESS, ArgusV2Components.SUN_SENSOR_ZP_I2C],
            "LIGHT_ZP_3": [ArgusV2Components.SUN_SENSOR_ZP3_I2C_ADDRESS, ArgusV2Components.SUN_SENSOR_ZP_I2C],
            "LIGHT_ZP_4": [ArgusV2Components.SUN_SENSOR_ZP4_I2C_ADDRESS, ArgusV2Components.SUN_SENSOR_ZP_I2C],
        }

        from hal.drivers.opt4003 import OPT4003

        data = directions[direction]

        try:
            address = data[0]
            bus = data[1]
            light_sensor = OPT4003(
                bus,
                address,
                conversion_time=ArgusV2Components.LIGHT_SENSOR_CONVERSION_TIME,
            )
            return [light_sensor, Errors.NO_ERROR]

        except Exception as e:
            if self.__debug:
                raise e
            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __radio_boot(self, _) -> list[object, int]:
        """radio_boot: Boot sequence for the radio

        :return: Error code if the radio failed to initialize
        """

        from hal.drivers.sx126x import SX1262

        try:
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
                freq=435,
                bw=125,
                sf=7,
                cr=5,
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

            return [radio, Errors.NO_ERROR]

        except Exception as e:
            if self.__debug:
                raise e

            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __rtc_boot(self, _) -> list[object, int]:
        """rtc_boot: Boot sequence for the RTC

        :return: Error code if the RTC failed to initialize
        """

        from hal.drivers.ds3231 import DS3231

        try:
            rtc = DS3231(ArgusV2Components.RTC_I2C, ArgusV2Components.RTC_I2C_ADDRESS)
            return [rtc, Errors.NO_ERROR]
        except Exception as e:
            if self.__debug:
                raise e

            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __sd_card_boot(self, _) -> list[object, int]:
        """sd_card_boot: Boot sequence for the SD card"""
        try:
            sd_card = SDCard(
                ArgusV2Components.SD_CARD_SPI,
                ArgusV2Components.SD_CARD_CS,
                ArgusV2Components.SD_BAUD,
            )

            vfs = VfsFat(sd_card)
            mount(vfs, ArgusV2Components.VFS_MOUNT_POINT)
            path.append(ArgusV2Components.VFS_MOUNT_POINT)
            return [vfs, Errors.NO_ERROR]
        except Exception as e:
            if self.__debug:
                raise e

            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __burn_wire_boot(self, _) -> list[object, int]:
        """burn_wire_boot: Boot sequence for the burn wires"""
        try:
            # TODO: Burnwire software module
            from hal.drivers.burnwire import BurnWires

            burn_wires = BurnWires(
                ArgusV2Components.BURN_WIRE_ENABLE,
                ArgusV2Components.BURN_WIRE_XP,
                ArgusV2Components.BURN_WIRE_XM,
                ArgusV2Components.BURN_WIRE_YP,
                ArgusV2Components.BURN_WIRE_YM,
            )

            return [burn_wires, Errors.NO_ERROR]
        except Exception as e:
            if self.__debug:
                raise e

            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __fuel_gauge_boot(self, _) -> list[object, int]:
        """fuel_gauge_boot: Boot sequence for the fuel gauge"""

        from hal.drivers.max17205 import MAX17205

        try:
            fuel_gauge = MAX17205(
                ArgusV2Components.FUEL_GAUGE_I2C,
                ArgusV2Components.FUEL_GAUGE_I2C_ADDRESS,
            )

            return [fuel_gauge, Errors.NO_ERROR]
        except Exception as e:
            if self.__debug:
                raise e
            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __battery_heaters_boot(self, _) -> list[object, int]:
        return [None, Errors.NO_ERROR]

    def __watchdog_boot(self, _) -> list[object, int]:
        return [None, Errors.NO_ERROR]

    def __deployment_sensor_boot(self, _) -> list[object, int]:
        """deployment_sensor_boot: Boot sequence for the deployment sensor"""

        return [None, Errors.NO_ERROR]

    ######################## ERROR HANDLING ########################

    def check_device_dead(self, _: int) -> bool:
        return False

    def handle_error(self, _: str) -> int:
        return Errors.NO_REBOOT

    def graceful_reboot_devices(self, device_name):
        pass

    def reboot(self):
        import supervisor

        supervisor.reload()
