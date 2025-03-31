"""
Author: Harry, Thomas, Ibrahima, Perrin
Description: This file contains the definition of the ArgusV3 class and its associated interfaces and components.
"""

import time
from sys import path

import board
import digitalio
from busio import I2C, SPI, UART
from hal.cubesat import ASIL1, ASIL2, ASIL3, ASIL4, CubeSat
from hal.drivers.errors import Errors
from micropython import const
from sdcardio import SDCard
from storage import VfsFat, mount


class ArgusV3Power:
    #########
    # eFUSE #
    #########

    # PERIPHERALS 3.3V
    PERIPH_PWR_EN = digitalio.DigitalInOut(board.PERIPH_PWR_EN)
    PERIPH_PWR_EN.direction = digitalio.Direction.OUTPUT
    PERIPH_PWR_EN.value = True

    PERIPH_PWR_OVC = digitalio.DigitalInOut(board.PERIPH_PWR_FLT)
    PERIPH_PWR_OVC.direction = digitalio.Direction.INPUT

    # DO NOT MOVE
    time.sleep(2)  # Wait for peripherals to power up

    # MAIN (MCU, WATCHDOG) 3.3V
    MAIN_PWR_RESET = digitalio.DigitalInOut(board.MAIN_PWR_RST)
    MAIN_PWR_RESET.direction = digitalio.Direction.OUTPUT

    # GPS
    GPS_EN = digitalio.DigitalInOut(board.GPS_EN)
    GPS_EN.direction = digitalio.Direction.OUTPUT
    GPS_EN.value = True

    RADIO_EN = digitalio.DigitalInOut(board.LORA_EN)
    RADIO_EN.direction = digitalio.Direction.OUTPUT
    RADIO_EN.value = True

    COIL_EN = digitalio.DigitalInOut(board.COIL_EN)
    COIL_EN.direction = digitalio.Direction.OUTPUT
    COIL_EN.value = True

    BATT_HEAT_EN = digitalio.DigitalInOut(board.HEAT_EN)
    BATT_HEAT_EN.direction = digitalio.Direction.OUTPUT
    BATT_HEAT_EN.value = False

    BATT_HEATER0_ON = digitalio.DigitalInOut(board.HEAT0_ON)
    BATT_HEATER0_ON.direction = digitalio.Direction.OUTPUT
    BATT_HEATER0_ON.value = False

    BATT_HEATER1_ON = digitalio.DigitalInOut(board.HEAT1_ON)
    BATT_HEATER1_ON.direction = digitalio.Direction.OUTPUT
    BATT_HEATER1_ON.value = False


class ArgusV3Interfaces:
    """
    This class represents the interfaces used in the ArgusV3 module.
    """

    I2C0_SDA = board.SDA0
    I2C0_SCL = board.SCL0

    # Line may not be connected, try except sequence
    try:
        I2C0 = I2C(I2C0_SCL, I2C0_SDA, frequency=400000)
    except Exception:
        I2C0 = None

    I2C1_SDA = board.SDA1
    I2C1_SCL = board.SCL1

    # Line may not be connected, try except sequence
    try:
        I2C1 = I2C(I2C1_SCL, I2C1_SDA, frequency=400000)
    except Exception:
        I2C1 = None

    SPI0_SCK = board.CLK0
    SPI0_MOSI = board.MOSI0
    SPI0_MISO = board.MISO0
    SPI0 = SPI(SPI0_SCK, MOSI=SPI0_MOSI, MISO=SPI0_MISO)

    SPI1_SCK = board.CLK1
    SPI1_MOSI = board.MOSI1
    SPI1_MISO = board.MISO1
    SPI1 = SPI(SPI1_SCK, MOSI=SPI1_MOSI, MISO=SPI1_MISO)

    UART0_BAUD = const(115200)
    UART0_TX = board.TX0
    UART0_RX = board.RX0
    UART0 = UART(UART0_TX, UART0_RX, baudrate=UART0_BAUD)

    JETSON_BAUD = const(57600)
    JETSON_TX = board.TX1
    JETSON_RX = board.RX1
    JETSON_UART = UART(JETSON_TX, JETSON_RX, baudrate=JETSON_BAUD)


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

    # IMU
    IMU_I2C = ArgusV3Interfaces.I2C0
    IMU_I2C_ADDRESS = const(0x4A)

    # XM TORQUE COILS
    TORQUE_COILS_XM_I2C = ArgusV3Interfaces.I2C0
    TORQUE_XM_I2C_ADDRESS = const(0x30)

    # XM SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_XM_POWER_MONITOR_I2C = ArgusV3Interfaces.I2C0
    SOLAR_CHARGING_XM_POWER_MONITOR_I2C_ADDRESS = const(0x40)

    # XM LIGHT SENSOR
    LIGHT_SENSOR_XM_I2C = ArgusV3Interfaces.I2C0
    LIGHT_SENSOR_XM_I2C_ADDRESS = const(0x44)

    # YM TORQUE COILS
    TORQUE_COILS_YM_I2C = ArgusV3Interfaces.I2C0
    TORQUE_YM_I2C_ADDRESS = const(0x31)

    # YM SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_YM_POWER_MONITOR_I2C = ArgusV3Interfaces.I2C0
    SOLAR_CHARGING_YM_POWER_MONITOR_I2C_ADDRESS = const(0x41)

    # YM LIGHT SENSOR
    LIGHT_SENSOR_YM_I2C = ArgusV3Interfaces.I2C0
    LIGHT_SENSOR_YM_I2C_ADDRESS = const(0x45)

    # ZM TORQUE COILS
    TORQUE_COILS_ZM_I2C = ArgusV3Interfaces.I2C0
    TORQUE_ZM_I2C_ADDRESS = const(0x32)

    # ZM LIGHT SENSOR
    LIGHT_SENSOR_ZM_I2C = ArgusV3Interfaces.I2C0
    LIGHT_SENSOR_ZM_I2C_ADDRESS = const(0x46)

    # ZM BURN WIRE DRIVER
    BURN_WIRE_I2C = ArgusV3Interfaces.I2C0
    BURN_WIRE_I2C_ADDRESS = const(0x60)

    ########
    # I2C1 #
    ########

    # BOARD POWER MONITOR
    BOARD_POWER_MONITOR_I2C = ArgusV3Interfaces.I2C1
    BOARD_POWER_MONITOR_I2C_ADDRESS = const(0x40)

    # GPS POWER MONITOR
    GPS_POWER_MONITOR_I2C = ArgusV3Interfaces.I2C1
    GPS_POWER_MONITOR_I2C_ADDRESS = const(0x41)

    # LORA POWER MONITOR
    RADIO_POWER_MONITOR_I2C = ArgusV3Interfaces.I2C1
    RADIO_POWER_MONITOR_I2C_ADDRESS = const(0x42)

    # JETSON POWER MONITOR
    JETSON_POWER_MONITOR_I2C = ArgusV3Interfaces.I2C1
    JETSON_POWER_MONITOR_I2C_ADDRESS = const(0x43)

    # RTC
    RTC_I2C = ArgusV3Interfaces.I2C1
    RTC_I2C_ADDRESS = const(0x68)

    # XP TORQUE COILS
    TORQUE_COILS_XP_I2C = ArgusV3Interfaces.I2C1
    TORQUE_XP_I2C_ADDRESS = const(0x30)

    # XP SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_XP_POWER_MONITOR_I2C = ArgusV3Interfaces.I2C1
    SOLAR_CHARGING_XP_POWER_MONITOR_I2C_ADDRESS = const(0x48)

    # XP LIGHT SENSOR
    LIGHT_SENSOR_XP_I2C = ArgusV3Interfaces.I2C1
    LIGHT_SENSOR_XP_I2C_ADDRESS = const(0x44)

    # YP TORQUE COILS
    TORQUE_COILS_YP_I2C = ArgusV3Interfaces.I2C1
    TORQUE_YP_I2C_ADDRESS = const(0x31)

    # YP SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_YP_POWER_MONITOR_I2C = ArgusV3Interfaces.I2C1
    SOLAR_CHARGING_YP_POWER_MONITOR_I2C_ADDRESS = const(0x4A)

    # YP LIGHT SENSOR
    LIGHT_SENSOR_YP_I2C = ArgusV3Interfaces.I2C1
    LIGHT_SENSOR_YP_I2C_ADDRESS = const(0x45)

    # ZP TORQUE COILS
    TORQUE_COILS_ZP_I2C = ArgusV3Interfaces.I2C1
    TORQUE_ZP_I2C_ADDRESS = const(0x12)

    # ZP SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_ZP_POWER_MONITOR_I2C = ArgusV3Interfaces.I2C1
    SOLAR_CHARGING_ZP_POWER_MONITOR_I2C_ADDRESS = const(0x62)

    # ZP SUN SENSOR
    SUN_SENSOR_ZP_I2C = ArgusV3Interfaces.I2C1
    SUN_SENSOR_ZP1_I2C_ADDRESS = const(0x64)
    SUN_SENSOR_ZP2_I2C_ADDRESS = const(0x65)
    SUN_SENSOR_ZP3_I2C_ADDRESS = const(0x66)
    SUN_SENSOR_ZP4_I2C_ADDRESS = const(0x67)

    # BATTERY BOARD FUEL GAUGE
    FUEL_GAUGE_I2C = ArgusV3Interfaces.I2C1
    FUEL_GAUGE_I2C_ADDRESS = const(0x36)
    FUEL_GAUGE_ALERT = board.BATT_ALRT

    ########
    # SPI0 #
    ########

    # RADIO
    RADIO_SPI = ArgusV3Interfaces.SPI0
    RADIO_CS = board.LORA_nCS
    RADIO_RESET = board.LORA_nRST
    RADIO_TX_EN = board.LORA_TX_EN
    RADIO_RX_EN = board.LORA_RX_EN
    RADIO_BUSY = board.LORA_BUSY
    RADIO_IRQ = board.LORA_INT
    RADIO_OVC = digitalio.DigitalInOut(board.LORA_FLT)
    RADIO_OVC.direction = digitalio.Direction.INPUT

    ########
    # SPI1 #
    ########

    # SD CARD
    SD_CARD_SPI = ArgusV3Interfaces.SPI1
    SD_CARD_CS = board.SD_CS
    SD_BAUD = const(4000000)  # 4 MHz

    # Payload
    PAYLOAD_IO0 = board.PAYLOAD_IO0
    PAYLOAD_IO1 = board.PAYLOAD_IO1
    PAYLOAD_IO2 = board.PAYLOAD_IO2
    PAYLOAD_CS = board.PAYLOAD_nCS
    PAYLOAD_EN = board.PAYLOAD_EN
    PAYLOAD_FLT = digitalio.DigitalInOut(board.PAYLOAD_FLT)
    PAYLOAD_FLT.direction = digitalio.Direction.INPUT

    #########
    # UART0 #
    #########

    # GPS
    GPS_UART = ArgusV3Interfaces.UART0
    GPS_OVC = digitalio.DigitalInOut(board.GPS_FLT)
    GPS_OVC.direction = digitalio.Direction.INPUT

    #########
    # UART1 #
    #########

    # JETSON
    JETSON_UART = ArgusV3Interfaces.JETSON_UART
    JETSON_ENABLE = digitalio.DigitalInOut(board.JETSON_EN)
    JETSON_ENABLE.direction = digitalio.Direction.OUTPUT

    ########
    # MISC #
    ########

    # NEOPIXEL
    NEOPIXEL_SDA = board.NEOPIXEL
    NEOPIXEL_N = const(1)
    NEOPIXEL_BRIGHTNESS = 0.2

    # REACTION WHEEL
    RW_ENABLE = board.RW_EN

    # VFS
    VFS_MOUNT_POINT = "/sd"

    LIGHT_SENSOR_CONVERSION_TIME = 0b0000


class ArgusV3(CubeSat):
    """ArgusV3: Represents the Argus V3 CubeSat."""

    def __init__(self, debug: bool = False):
        """__init__: Initializes the Argus V3 CubeSat."""
        self.__debug = debug

        super().__init__()

        self.__payload_uart = ArgusV3Interfaces.JETSON_UART

    ######################## BOOT SEQUENCE ########################

    def __boot_device(self, name: str, device: object):
        func = device.boot_fn
        device.device, device.error = func(name)

    def boot_sequence(self):
        """boot_sequence: Boot sequence for the CubeSat."""

        for name, device in self.__device_list.items():
            self.__boot_device(name, device)

    def __gps_boot(self, _) -> list[object, int]:
        """GPS_boot: Boot sequence for the GPS

        :return: Error code if the GPS failed to initialize
        """

        from hal.drivers.gps import GPS

        try:
            gps = GPS(ArgusV3Components.GPS_UART, None, False, False)

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
            "BOARD_PWR": [ArgusV3Components.BOARD_POWER_MONITOR_I2C_ADDRESS, ArgusV3Components.BOARD_POWER_MONITOR_I2C],
            "RADIO_PWR": [ArgusV3Components.RADIO_POWER_MONITOR_I2C_ADDRESS, ArgusV3Components.RADIO_POWER_MONITOR_I2C],
            "GPS_PWR": [ArgusV3Components.GPS_POWER_MONITOR_I2C_ADDRESS, ArgusV3Components.GPS_POWER_MONITOR_I2C],
            "JETSON_PWR": [ArgusV3Components.JETSON_POWER_MONITOR_I2C_ADDRESS, ArgusV3Components.JETSON_POWER_MONITOR_I2C],
            "XP_PWR": [
                ArgusV3Components.SOLAR_CHARGING_XP_POWER_MONITOR_I2C_ADDRESS,
                ArgusV3Components.SOLAR_CHARGING_XP_POWER_MONITOR_I2C,
            ],
            "XM_PWR": [
                ArgusV3Components.SOLAR_CHARGING_XM_POWER_MONITOR_I2C_ADDRESS,
                ArgusV3Components.SOLAR_CHARGING_XM_POWER_MONITOR_I2C,
            ],
            "YP_PWR": [
                ArgusV3Components.SOLAR_CHARGING_YP_POWER_MONITOR_I2C_ADDRESS,
                ArgusV3Components.SOLAR_CHARGING_YP_POWER_MONITOR_I2C,
            ],
            "YM_PWR": [
                ArgusV3Components.SOLAR_CHARGING_YM_POWER_MONITOR_I2C_ADDRESS,
                ArgusV3Components.SOLAR_CHARGING_YM_POWER_MONITOR_I2C,
            ],
            "ZP_PWR": [
                ArgusV3Components.SOLAR_CHARGING_ZP_POWER_MONITOR_I2C_ADDRESS,
                ArgusV3Components.SOLAR_CHARGING_ZP_POWER_MONITOR_I2C,
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
                ArgusV3Components.IMU_I2C,
                ArgusV3Components.IMU_I2C_ADDRESS,
            )
            imu.enable_feature(BNO_REPORT_UNCAL_MAGNETOMETER)
            imu.enable_feature(BNO_REPORT_UNCAL_GYROSCOPE)

            return [imu, Errors.NO_ERROR]
        except Exception as e:
            print(e)
            if self.__debug:
                raise e
            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __torque_driver_boot(self, direction) -> list[int]:
        """Boot sequence for all torque drivers in predefined directions.

        :return: List of error codes for each torque driver in the order of directions
        """
        directions = {
            "TORQUE_XP": [ArgusV3Components.TORQUE_XP_I2C_ADDRESS, ArgusV3Components.TORQUE_COILS_XP_I2C],
            "TORQUE_XM": [ArgusV3Components.TORQUE_XM_I2C_ADDRESS, ArgusV3Components.TORQUE_COILS_XM_I2C],
            "TORQUE_YP": [ArgusV3Components.TORQUE_YP_I2C_ADDRESS, ArgusV3Components.TORQUE_COILS_YP_I2C],
            "TORQUE_YM": [ArgusV3Components.TORQUE_YM_I2C_ADDRESS, ArgusV3Components.TORQUE_COILS_YM_I2C],
            "TORQUE_ZP": [ArgusV3Components.TORQUE_ZP_I2C_ADDRESS, ArgusV3Components.TORQUE_COILS_ZP_I2C],
            "TORQUE_ZM": [ArgusV3Components.TORQUE_ZM_I2C_ADDRESS, ArgusV3Components.TORQUE_COILS_ZM_I2C],
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
            "LIGHT_XP": [ArgusV3Components.LIGHT_SENSOR_XP_I2C_ADDRESS, ArgusV3Components.LIGHT_SENSOR_XP_I2C],
            "LIGHT_XM": [ArgusV3Components.LIGHT_SENSOR_XM_I2C_ADDRESS, ArgusV3Components.LIGHT_SENSOR_XM_I2C],
            "LIGHT_YP": [ArgusV3Components.LIGHT_SENSOR_YP_I2C_ADDRESS, ArgusV3Components.LIGHT_SENSOR_YP_I2C],
            "LIGHT_YM": [ArgusV3Components.LIGHT_SENSOR_YM_I2C_ADDRESS, ArgusV3Components.LIGHT_SENSOR_YM_I2C],
            "LIGHT_ZM": [ArgusV3Components.LIGHT_SENSOR_ZM_I2C_ADDRESS, ArgusV3Components.LIGHT_SENSOR_ZM_I2C],
            "LIGHT_ZP_1": [ArgusV3Components.SUN_SENSOR_ZP1_I2C_ADDRESS, ArgusV3Components.SUN_SENSOR_ZP_I2C],
            "LIGHT_ZP_2": [ArgusV3Components.SUN_SENSOR_ZP2_I2C_ADDRESS, ArgusV3Components.SUN_SENSOR_ZP_I2C],
            "LIGHT_ZP_3": [ArgusV3Components.SUN_SENSOR_ZP3_I2C_ADDRESS, ArgusV3Components.SUN_SENSOR_ZP_I2C],
            "LIGHT_ZP_4": [ArgusV3Components.SUN_SENSOR_ZP4_I2C_ADDRESS, ArgusV3Components.SUN_SENSOR_ZP_I2C],
        }

        from hal.drivers.opt4003 import OPT4003

        data = directions[direction]

        try:
            address = data[0]
            bus = data[1]
            light_sensor = OPT4003(
                bus,
                address,
                conversion_time=ArgusV3Components.LIGHT_SENSOR_CONVERSION_TIME,
            )
            return [light_sensor, Errors.NO_ERROR]

        except Exception as e:
            print(e)
            if self.__debug:
                raise e
            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __radio_boot(self, _) -> list[object, int]:
        """radio_boot: Boot sequence for the radio

        :return: Error code if the radio failed to initialize
        """

        from hal.drivers.sx126x import SX1262

        try:
            radio = SX1262(
                spi_bus=ArgusV3Components.RADIO_SPI,
                cs=ArgusV3Components.RADIO_CS,
                irq=ArgusV3Components.RADIO_IRQ,
                rst=ArgusV3Components.RADIO_RESET,
                gpio=ArgusV3Components.RADIO_BUSY,
                tx_en=ArgusV3Components.RADIO_TX_EN,
                rx_en=ArgusV3Components.RADIO_RX_EN,
            )

            radio.begin(
                freq=433,
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
            rtc = DS3231(ArgusV3Components.RTC_I2C, ArgusV3Components.RTC_I2C_ADDRESS)
            return [rtc, Errors.NO_ERROR]
        except Exception as e:
            if self.__debug:
                raise e

            return [None, Errors.DEVICE_NOT_INITIALISED]

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
            return [vfs, Errors.NO_ERROR]
        except Exception as e:
            if self.__debug:
                raise e

            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __burn_wire_boot(self, _) -> list[object, int]:
        """burn_wire_boot: Boot sequence for the burn wires"""
        from hal.drivers.pca9633 import PCA9633

        try:
            burn_wires = PCA9633(
                ArgusV3Components.BURN_WIRE_I2C,
                ArgusV3Components.BURN_WIRE_I2C_ADDRESS,
            )
            return [burn_wires, Errors.NOERROR]
        except Exception as e:
            if self.__debug:
                raise e

            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __fuel_gauge_boot(self, _) -> list[object, int]:
        """fuel_gauge_boot: Boot sequence for the fuel gauge"""

        from hal.drivers.max17205 import MAX17205

        try:
            fuel_gauge = MAX17205(
                ArgusV3Components.FUEL_GAUGE_I2C,
                ArgusV3Components.FUEL_GAUGE_I2C_ADDRESS,
            )

            return [fuel_gauge, Errors.NO_ERROR]
        except Exception as e:
            if self.__debug:
                raise e
            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __neopixel_boot(self, _) -> list[object, int]:
        """neopixel_boot: Boot sequence for the neopixel"""
        import neopixel

        try:
            np = neopixel.NeoPixel(
                ArgusV3Components.NEOPIXEL_SDA,
                ArgusV3Components.NEOPIXEL_N,
                brightness=ArgusV3Components.NEOPIXEL_BRIGHTNESS,
                pixel_order=neopixel.GRB,
            )
            np.fill((128, 128, 128))
            return [np, Errors.NO_ERROR]
        except Exception as e:
            if self.__debug:
                raise e

            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __restart_power_line(self, power_line):
        power_line.value = False
        time.sleep(0.5)
        power_line.value = True

    def __reboot_device(self, device_name: str):

        device = self.__device_list[device_name]
        if device_name == "RADIO":
            device.deinit()
            self.__restart_power_line(ArgusV3Power.RADIO_EN)
            self.__boot_device(device_name, device)
        elif device_name == "GPS":
            device.deinit()
            self.__restart_power_line(ArgusV3Power.GPS_EN)
            self.__boot_device(device_name, device)
        else:
            self.__restart_power_line(ArgusV3Power.PERIPH_PWR_EN)
        # TODO: Implement reboot logic

    def handle_error(self, device_name: str) -> int:
        if device_name not in self.__device_list:
            return Errors.INVALID_DEVICE_NAME
        self.__device_list[device_name].error_count += 1
        ASIL = self.__device_list[device_name].ASIL
        if ASIL == ASIL4:
            self.__reboot_device(device_name)
        elif ASIL == ASIL3:
            return Errors.DEVICE_NOT_INITIALISED
        elif ASIL == "ASIL_C":
            return Errors.DEVICE_NOT_INITIALISED
        else:
            return Errors.DEVICE_NOT_INITIALISED

    def REBOOT(self):
        """Reboot the satellite by resetting the main power."""
        ArgusV3Power.MAIN_PWR_RESET.value = True
