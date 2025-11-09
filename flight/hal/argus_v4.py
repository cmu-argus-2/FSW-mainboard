"""
Author: Perrin
Description: This file contains the definition of the ArgusV4 class and its associated interfaces and components.
"""

import time

import board
import digitalio
from busio import I2C, SPI, UART
from hal.cubesat import ASIL0, ASIL1, ASIL2, ASIL3, ASIL4, CubeSat
from hal.drivers.errors import Errors
from hal.drivers.objectWrapper import objectWrapper
from micropython import const
from sdcardio import SDCard


class ArgusV4Power:
    #########
    # eFUSE #
    #########

    # PERIPHERALS 3.3V
    PERIPH_PWR_EN = digitalio.DigitalInOut(board.PERIPH_PWR_EN)
    PERIPH_PWR_EN.direction = digitalio.Direction.OUTPUT
    PERIPH_PWR_EN.value = True

    PERIPH_PWR_OVC = digitalio.DigitalInOut(board.PERIPH_PWR_FLT)
    PERIPH_PWR_OVC.direction = digitalio.Direction.INPUT

    """
    Peripherlas 3.3V must be enabled before accessing I2C devices
    to ensure addresses are correct as we have different address configurations
    """
    time.sleep(0.1)  # Wait for peripherals to power up

    # MAIN (MCU, WATCHDOG) 3.3V
    MAIN_PWR_RESET = digitalio.DigitalInOut(board.MAIN_PWR_RST)
    MAIN_PWR_RESET.direction = digitalio.Direction.OUTPUT

    # GPS
    GPS_EN = digitalio.DigitalInOut(board.GPS_EN)
    GPS_EN.direction = digitalio.Direction.OUTPUT
    GPS_EN.value = True

    GPS_OVC = digitalio.DigitalInOut(board.GPS_FLT)
    GPS_OVC.direction = digitalio.Direction.INPUT

    RADIO_EN = digitalio.DigitalInOut(board.LORA_EN)
    RADIO_EN.direction = digitalio.Direction.OUTPUT
    RADIO_EN.value = True

    RADIO_OVC = digitalio.DigitalInOut(board.LORA_FLT)
    RADIO_OVC.direction = digitalio.Direction.INPUT

    COIL_EN = digitalio.DigitalInOut(board.COIL_EN)
    COIL_EN.direction = digitalio.Direction.OUTPUT
    COIL_EN.value = True

    BATT_HEAT_EN = board.HEAT_EN
    BATT_HEATER0_EN = board.HEAT0_ON
    BATT_HEATER1_EN = board.HEAT1_ON

    # PAYLOAD_OVC = digitalio.DigitalInOut(board.PAYLOAD_FLT)
    # PAYLOAD_OVC.direction = digitalio.Direction.INPUT


class ArgusV4Interfaces:
    """
    This class represents the interfaces used in the ArgusV4 module.
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


class ArgusV4Components:
    """
    Represents the components used in the Argus V4 system.

    This class defines constants for various components such as GPS, battery,
    power monitor, Jetson power monitor, IMU, charger, torque coils,
    light sensors, radio, and SD card.
    """

    ########
    # I2C0 #
    ########

    # IMU
    IMU_I2C = ArgusV4Interfaces.I2C0
    IMU_I2C_ADDRESS = const(0x68)

    # XM TORQUE COILS
    TORQUE_COILS_XM_I2C = ArgusV4Interfaces.I2C0
    TORQUE_XM_I2C_ADDRESS = const(0x30)

    # XM SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_XM_POWER_MONITOR_I2C = ArgusV4Interfaces.I2C0
    SOLAR_CHARGING_XM_POWER_MONITOR_I2C_ADDRESS = const(0x40)

    # XM LIGHT SENSOR
    LIGHT_SENSOR_XM_I2C = ArgusV4Interfaces.I2C0
    LIGHT_SENSOR_XM_I2C_ADDRESS = const(0x44)

    # YM TORQUE COILS
    TORQUE_COILS_YM_I2C = ArgusV4Interfaces.I2C0
    TORQUE_YM_I2C_ADDRESS = const(0x31)

    # YM SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_YM_POWER_MONITOR_I2C = ArgusV4Interfaces.I2C0
    SOLAR_CHARGING_YM_POWER_MONITOR_I2C_ADDRESS = const(0x41)

    # YM LIGHT SENSOR
    LIGHT_SENSOR_YM_I2C = ArgusV4Interfaces.I2C0
    LIGHT_SENSOR_YM_I2C_ADDRESS = const(0x45)

    # ZM TORQUE COILS
    TORQUE_COILS_ZM_I2C = ArgusV4Interfaces.I2C0
    TORQUE_ZM_I2C_ADDRESS = const(0x32)

    # ZM LIGHT SENSOR
    LIGHT_SENSOR_ZM_I2C = ArgusV4Interfaces.I2C0
    LIGHT_SENSOR_ZM_I2C_ADDRESS = const(0x46)

    # ZM BURN WIRE DRIVER
    BURN_WIRE_I2C = ArgusV4Interfaces.I2C0
    BURN_WIRE_I2C_ADDRESS = const(0x60)

    # YM DEPLOYMENT SENSOR
    DEPLOYMENT_SENSOR_YM_I2C = ArgusV4Interfaces.I2C0
    DEPLOYMENT_SENSOR_YM_I2C_ADDRESS = const(0x29)

    ########
    # I2C1 #
    ########

    # BOARD POWER MONITOR
    BOARD_POWER_MONITOR_I2C = ArgusV4Interfaces.I2C1
    BOARD_POWER_MONITOR_I2C_ADDRESS = const(0x40)

    # GPS POWER MONITOR
    GPS_POWER_MONITOR_I2C = ArgusV4Interfaces.I2C1
    GPS_POWER_MONITOR_I2C_ADDRESS = const(0x41)

    # LORA POWER MONITOR
    RADIO_POWER_MONITOR_I2C = ArgusV4Interfaces.I2C1
    RADIO_POWER_MONITOR_I2C_ADDRESS = const(0x42)

    # JETSON POWER MONITOR
    JETSON_POWER_MONITOR_I2C = ArgusV4Interfaces.I2C1
    JETSON_POWER_MONITOR_I2C_ADDRESS = const(0x43)

    # RTC
    RTC_I2C = ArgusV4Interfaces.I2C1
    RTC_I2C_ADDRESS = const(0x68)

    # XP TORQUE COILS
    TORQUE_COILS_XP_I2C = ArgusV4Interfaces.I2C1
    TORQUE_XP_I2C_ADDRESS = const(0x30)

    # XP SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_XP_POWER_MONITOR_I2C = ArgusV4Interfaces.I2C1
    SOLAR_CHARGING_XP_POWER_MONITOR_I2C_ADDRESS = const(0x48)

    # XP LIGHT SENSOR
    LIGHT_SENSOR_XP_I2C = ArgusV4Interfaces.I2C1
    LIGHT_SENSOR_XP_I2C_ADDRESS = const(0x44)

    # YP TORQUE COILS
    TORQUE_COILS_YP_I2C = ArgusV4Interfaces.I2C1
    TORQUE_YP_I2C_ADDRESS = const(0x31)

    # YP SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_YP_POWER_MONITOR_I2C = ArgusV4Interfaces.I2C1
    SOLAR_CHARGING_YP_POWER_MONITOR_I2C_ADDRESS = const(0x4A)

    # YP LIGHT SENSOR
    LIGHT_SENSOR_YP_I2C = ArgusV4Interfaces.I2C1
    LIGHT_SENSOR_YP_I2C_ADDRESS = const(0x45)

    # ZP TORQUE COILS
    TORQUE_COILS_ZP_I2C = ArgusV4Interfaces.I2C1
    TORQUE_ZP_I2C_ADDRESS = const(0x12)

    # ZP SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_ZP_POWER_MONITOR_I2C = ArgusV4Interfaces.I2C1
    SOLAR_CHARGING_ZP_POWER_MONITOR_I2C_ADDRESS = const(0x62)

    # ZP SUN SENSOR
    SUN_SENSOR_ZP_I2C = ArgusV4Interfaces.I2C1
    SUN_SENSOR_ZP1_I2C_ADDRESS = const(0x64)
    SUN_SENSOR_ZP2_I2C_ADDRESS = const(0x65)
    SUN_SENSOR_ZP3_I2C_ADDRESS = const(0x66)
    SUN_SENSOR_ZP4_I2C_ADDRESS = const(0x67)

    # BATTERY BOARD FUEL GAUGE
    FUEL_GAUGE_I2C = ArgusV4Interfaces.I2C1
    FUEL_GAUGE_I2C_ADDRESS = const(0x36)
    FUEL_GAUGE_ALERT = board.BATT_ALRT

    # XP DEPLOYMENT SENSOR
    DEPLOYMENT_SENSOR_XP_I2C = ArgusV4Interfaces.I2C1
    DEPLOYMENT_SENSOR_XP_I2C_ADDRESS = const(0x29)

    ########
    # SPI0 #
    ########

    # RADIO
    RADIO_SPI = ArgusV4Interfaces.SPI0
    RADIO_CS = board.LORA_nCS
    RADIO_RESET = board.LORA_nRST
    RADIO_TX_EN = board.LORA_TX_EN
    RADIO_RX_EN = board.LORA_RX_EN
    RADIO_BUSY = board.LORA_BUSY
    RADIO_IRQ = board.LORA_INT

    ########
    # SPI1 #
    ########

    # SD CARD
    SD_CARD_SPI = ArgusV4Interfaces.SPI1
    SD_CARD_CS = board.SD_CS
    SD_BAUD = const(4000000)  # 4 MHz

    # Payload
    # PAYLOAD_IO0 = board.PAYLOAD_IO0
    # PAYLOAD_IO1 = board.PAYLOAD_IO1
    # PAYLOAD_IO2 = board.PAYLOAD_IO2
    JETSON_SD_REQ = board.JETSON_SD_REQ
    # PAYLOAD_CS = board.PAYLOAD_nCS
    # PAYLOAD_EN = board.PAYLOAD_EN

    #########
    # UART0 #
    #########

    # GPS
    GPS_UART = ArgusV4Interfaces.UART0
    GPS_ENABLE = board.GPS_EN

    #########
    # UART1 #
    #########

    # JETSON
    JETSON_UART = ArgusV4Interfaces.JETSON_UART
    JETSON_ENABLE = digitalio.DigitalInOut(board.JETSON_EN)
    JETSON_ENABLE.direction = digitalio.Direction.OUTPUT

    ########
    # MISC #
    ########

    # NEOPIXEL
    NEOPIXEL_SDA = board.NEOPIXEL
    NEOPIXEL_N = const(1)
    NEOPIXEL_BRIGHTNESS = 0.2

    # WATCHDAWG
    WATCHDAWG_ENABLE = board.WDT_EN
    WATCHDAWG_INPUT = board.WDT_WDI

    # REACTION WHEEL
    RW_ENABLE = board.RW_EN

    LIGHT_SENSOR_CONVERSION_TIME = 0b0000


class ArgusV4(CubeSat):
    """ArgusV4: Represents the Argus V4 CubeSat."""

    def __init__(self, debug: bool = False):
        """__init__: Initializes the Argus V4 CubeSat."""
        self.__debug = debug

        super().__init__()

        self.__payload_uart = ArgusV4Interfaces.JETSON_UART

    ######################## BOOT SEQUENCE ########################

    def __boot_device(self, name: str, device: object):
        func = device.boot_fn
        device.device, device.error = func(name)
        if device.error == Errors.NO_ERROR and device.device is not None:
            device.device = objectWrapper(device.device)

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
            gps = GPS(ArgusV4Components.GPS_UART, None, False, False)

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
            "BOARD_PWR": [ArgusV4Components.BOARD_POWER_MONITOR_I2C_ADDRESS, ArgusV4Components.BOARD_POWER_MONITOR_I2C],
            "RADIO_PWR": [ArgusV4Components.RADIO_POWER_MONITOR_I2C_ADDRESS, ArgusV4Components.RADIO_POWER_MONITOR_I2C],
            "GPS_PWR": [ArgusV4Components.GPS_POWER_MONITOR_I2C_ADDRESS, ArgusV4Components.GPS_POWER_MONITOR_I2C],
            "JETSON_PWR": [ArgusV4Components.JETSON_POWER_MONITOR_I2C_ADDRESS, ArgusV4Components.JETSON_POWER_MONITOR_I2C],
            "XP_PWR": [
                ArgusV4Components.SOLAR_CHARGING_XP_POWER_MONITOR_I2C_ADDRESS,
                ArgusV4Components.SOLAR_CHARGING_XP_POWER_MONITOR_I2C,
            ],
            "XM_PWR": [
                ArgusV4Components.SOLAR_CHARGING_XM_POWER_MONITOR_I2C_ADDRESS,
                ArgusV4Components.SOLAR_CHARGING_XM_POWER_MONITOR_I2C,
            ],
            "YP_PWR": [
                ArgusV4Components.SOLAR_CHARGING_YP_POWER_MONITOR_I2C_ADDRESS,
                ArgusV4Components.SOLAR_CHARGING_YP_POWER_MONITOR_I2C,
            ],
            "YM_PWR": [
                ArgusV4Components.SOLAR_CHARGING_YM_POWER_MONITOR_I2C_ADDRESS,
                ArgusV4Components.SOLAR_CHARGING_YM_POWER_MONITOR_I2C,
            ],
            "ZP_PWR": [
                ArgusV4Components.SOLAR_CHARGING_ZP_POWER_MONITOR_I2C_ADDRESS,
                ArgusV4Components.SOLAR_CHARGING_ZP_POWER_MONITOR_I2C,
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

        # from hal.drivers.bno085 import BNO085, BNO_REPORT_UNCAL_GYROSCOPE, BNO_REPORT_UNCAL_MAGNETOMETER

        try:
            from hal.drivers.bmx160 import BMX160

            imu = BMX160(
                ArgusV4Components.IMU_I2C,
                ArgusV4Components.IMU_I2C_ADDRESS,
            )

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
            "TORQUE_XP": [ArgusV4Components.TORQUE_XP_I2C_ADDRESS, ArgusV4Components.TORQUE_COILS_XP_I2C],
            "TORQUE_XM": [ArgusV4Components.TORQUE_XM_I2C_ADDRESS, ArgusV4Components.TORQUE_COILS_XM_I2C],
            "TORQUE_YP": [ArgusV4Components.TORQUE_YP_I2C_ADDRESS, ArgusV4Components.TORQUE_COILS_YP_I2C],
            "TORQUE_YM": [ArgusV4Components.TORQUE_YM_I2C_ADDRESS, ArgusV4Components.TORQUE_COILS_YM_I2C],
            "TORQUE_ZP": [ArgusV4Components.TORQUE_ZP_I2C_ADDRESS, ArgusV4Components.TORQUE_COILS_ZP_I2C],
            "TORQUE_ZM": [ArgusV4Components.TORQUE_ZM_I2C_ADDRESS, ArgusV4Components.TORQUE_COILS_ZM_I2C],
        }
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
            "LIGHT_XP": [ArgusV4Components.LIGHT_SENSOR_XP_I2C_ADDRESS, ArgusV4Components.LIGHT_SENSOR_XP_I2C],
            "LIGHT_XM": [ArgusV4Components.LIGHT_SENSOR_XM_I2C_ADDRESS, ArgusV4Components.LIGHT_SENSOR_XM_I2C],
            "LIGHT_YP": [ArgusV4Components.LIGHT_SENSOR_YP_I2C_ADDRESS, ArgusV4Components.LIGHT_SENSOR_YP_I2C],
            "LIGHT_YM": [ArgusV4Components.LIGHT_SENSOR_YM_I2C_ADDRESS, ArgusV4Components.LIGHT_SENSOR_YM_I2C],
            "LIGHT_ZM": [ArgusV4Components.LIGHT_SENSOR_ZM_I2C_ADDRESS, ArgusV4Components.LIGHT_SENSOR_ZM_I2C],
            "LIGHT_ZP_1": [ArgusV4Components.SUN_SENSOR_ZP1_I2C_ADDRESS, ArgusV4Components.SUN_SENSOR_ZP_I2C],
            "LIGHT_ZP_2": [ArgusV4Components.SUN_SENSOR_ZP2_I2C_ADDRESS, ArgusV4Components.SUN_SENSOR_ZP_I2C],
            "LIGHT_ZP_3": [ArgusV4Components.SUN_SENSOR_ZP3_I2C_ADDRESS, ArgusV4Components.SUN_SENSOR_ZP_I2C],
            "LIGHT_ZP_4": [ArgusV4Components.SUN_SENSOR_ZP4_I2C_ADDRESS, ArgusV4Components.SUN_SENSOR_ZP_I2C],
        }

        from hal.drivers.opt4003 import OPT4003

        data = directions[direction]

        try:
            address = data[0]
            bus = data[1]
            light_sensor = OPT4003(
                bus,
                address,
                conversion_time=ArgusV4Components.LIGHT_SENSOR_CONVERSION_TIME,
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
            radio = SX1262(
                spi_bus=ArgusV4Components.RADIO_SPI,
                cs=ArgusV4Components.RADIO_CS,
                irq=ArgusV4Components.RADIO_IRQ,
                rst=ArgusV4Components.RADIO_RESET,
                gpio=ArgusV4Components.RADIO_BUSY,
                tx_en=ArgusV4Components.RADIO_TX_EN,
                rx_en=ArgusV4Components.RADIO_RX_EN,
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
            rtc = DS3231(ArgusV4Components.RTC_I2C, ArgusV4Components.RTC_I2C_ADDRESS)
            return [rtc, Errors.NO_ERROR]
        except Exception as e:
            if self.__debug:
                raise e

            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __sd_card_boot(self, _) -> list[object, int]:
        """sd_card_boot: Boot sequence for the SD card"""

        from hal.drivers.sdcard import CustomVfsFat

        try:
            sd_card = SDCard(
                ArgusV4Components.SD_CARD_SPI,
                ArgusV4Components.SD_CARD_CS,
                ArgusV4Components.SD_BAUD,
            )

            vfs = CustomVfsFat(sd_card)
            return [vfs, Errors.NO_ERROR]
        except Exception as e:
            print(e)
            if self.__debug:
                raise e

            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __burn_wire_boot(self, _) -> list[object, int]:
        """burn_wire_boot: Boot sequence for the burn wires"""
        from hal.drivers.pca9633 import PCA9633

        try:
            burn_wires = PCA9633(
                ArgusV4Components.BURN_WIRE_I2C,
                ArgusV4Components.BURN_WIRE_I2C_ADDRESS,
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
                ArgusV4Components.FUEL_GAUGE_I2C,
                ArgusV4Components.FUEL_GAUGE_I2C_ADDRESS,
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
                ArgusV4Components.NEOPIXEL_SDA,
                ArgusV4Components.NEOPIXEL_N,
                brightness=ArgusV4Components.NEOPIXEL_BRIGHTNESS,
                pixel_order=neopixel.GRB,
            )
            np.fill((128, 128, 128))
            return [np, Errors.NO_ERROR]
        except Exception as e:
            if self.__debug:
                raise e

            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __battery_heaters_boot(self, _) -> list[object, int]:
        """battery_heaters_boot: Boot sequence for the battery heaters"""
        from hal.drivers.batteryheaters import BatteryHeaters

        try:
            battery_heaters = BatteryHeaters(
                ArgusV4Power.BATT_HEAT_EN,
                ArgusV4Power.BATT_HEATER0_EN,
                ArgusV4Power.BATT_HEATER1_EN,
            )
            return [battery_heaters, Errors.NO_ERROR]
        except Exception as e:
            if self.__debug:
                raise e

            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __watchdog_boot(self, _) -> list[object, int]:
        """watchdog_boot: Boot sequence for the watchdog"""
        from hal.drivers.watchdog import Watchdog as Watchdawg

        try:
            watchdawg = Watchdawg(
                ArgusV4Components.WATCHDAWG_ENABLE,
                ArgusV4Components.WATCHDAWG_INPUT,
            )
            return [watchdawg, Errors.NO_ERROR]
        except Exception as e:
            if self.__debug:
                raise e

            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __deployment_sensor_boot(self, direction) -> list[object, int]:
        """deployment_sensor_boot: Boot sequence for the deployment sensor"""
        from hal.drivers.vl53l4cd import VL53L4CD

        directions = {
            "DEPLOYMENT_XP": [ArgusV4Components.DEPLOYMENT_SENSOR_XP_I2C, ArgusV4Components.DEPLOYMENT_SENSOR_XP_I2C_ADDRESS],
            "DEPLOYMENT_YM": [ArgusV4Components.DEPLOYMENT_SENSOR_YM_I2C, ArgusV4Components.DEPLOYMENT_SENSOR_YM_I2C_ADDRESS],
        }

        data = directions[direction]

        try:
            bus = data[0]
            address = data[1]
            deployment_sensor = VL53L4CD(bus, address)
            deployment_sensor.timing_budget = 10
            deployment_sensor.start_ranging()
            return [deployment_sensor, Errors.NO_ERROR]
        except Exception as e:
            print(e)
            if self.__debug:
                raise e

            return [None, Errors.DEVICE_NOT_INITIALISED]

    ######################## ERROR HANDLING ########################

    def __turn_off_power_line(self, power_line):
        power_line.value = False

    def __turn_on_power_line(self, power_line):
        power_line.value = True

    def __turn_off_device(self, device_name: str):
        device_cls = self.__device_list[device_name]

        if device_name == "RADIO":
            device_cls.temp_disabled = True
            if device_cls.device is not None:
                device_cls.device.deinit()
            self.__turn_off_power_line(ArgusV4Power.RADIO_EN)

        elif device_name == "GPS":
            device_cls.temp_disabled = True
            if device_cls.device is not None:
                device_cls.device.deinit()
            self.__turn_off_power_line(ArgusV4Power.GPS_EN)

        elif device_name.startswith("TORQUE"):
            for location, device_cls in self.__device_list.items():
                if location.startswith("TORQUE"):
                    device_cls.temp_disabled = True
                    if device_cls.device is not None and not device_cls.dead:
                        device_cls.device.deinit()
            self.__turn_off_power_line(ArgusV4Power.COIL_EN)

        else:
            for location, device_cls in self.__device_list.items():
                if device_cls.peripheral_line and device_cls.device is not None and not device_cls.dead:
                    device_cls.temp_disabled = True
                    device_cls.device.deinit()
            self.__turn_off_power_line(ArgusV4Power.PERIPH_PWR_EN)

    def __turn_on_device(self, device_name: str):
        device_cls = self.__device_list[device_name]

        if device_name == "RADIO":
            self.__turn_on_power_line(ArgusV4Power.RADIO_EN)
            self.__boot_device(device_name, device_cls)
            device_cls.temp_disabled = False

        elif device_name == "GPS":
            self.__turn_on_power_line(ArgusV4Power.GPS_EN)
            self.__boot_device(device_name, device_cls)
            device_cls.temp_disabled = False

        elif device_name.startswith("TORQUE"):
            self.__turn_on_power_line(ArgusV4Power.COIL_EN)

            for location, device_cls in self.__device_list.items():
                if location.startswith("TORQUE"):
                    device_cls.temp_disabled = False
                    if not device_cls.dead:
                        self.__boot_device(location, device_cls)

        else:
            self.__turn_on_power_line(ArgusV4Power.PERIPH_PWR_EN)

            for location, device_cls in self.__device_list.items():
                if device_cls.peripheral_line and not device_cls.dead:
                    self.__boot_device(location, device_cls)
                    device_cls.temp_disabled = False

    def check_device_dead(self, error_count: int) -> bool:
        return error_count > ArgusV4Error.MAX_DEVICE_ERROR

    def handle_error(self, device_name: str) -> int:
        if device_name not in self.__device_list:
            return Errors.INVALID_DEVICE_NAME

        device_cls = self.__device_list[device_name]

        device_cls.error_count += 1
        if self.check_device_dead(device_cls.error_count):
            device_cls.dead = True
            device_cls.device = None
            return Errors.DEVICE_DEAD

        ASIL = device_cls.ASIL
        device_cls.temp_disabled = True

        if ASIL == ASIL4:
            if device_cls.peripheral_line:
                return Errors.GRACEFUL_REBOOT
            else:
                self.__turn_off_device(device_name)
                return Errors.REBOOT_DEVICE

        elif ASIL != ASIL0:
            if device_name.startswith("TORQUE"):
                ArgusV4Error.TORQUE_ERRORS[device_name] += 1
                if (
                    (ArgusV4Error.TORQUE_ERRORS["TORQUE_XP"] != 0 and ArgusV4Error.TORQUE_ERRORS["TORQUE_XM"] != 0)
                    or (ArgusV4Error.TORQUE_ERRORS["TORQUE_YP"] != 0 and ArgusV4Error.TORQUE_ERRORS["TORQUE_YM"] != 0)
                    or (ArgusV4Error.TORQUE_ERRORS["TORQUE_ZP"] != 0 and ArgusV4Error.TORQUE_ERRORS["TORQUE_ZM"] != 0)
                ):
                    for key in ArgusV4Error.TORQUE_ERRORS:
                        ArgusV4Error.TORQUE_ERRORS[key] = 0
                    self.__turn_off_device(device_name)
                    return Errors.REBOOT_DEVICE

            elif device_name.startswith("GPS"):
                ArgusV4Error.GPS_ERRORS += 1
                if ArgusV4Error.GPS_ERRORS >= ArgusV4Error.ASIL_THRESHOLDS[ASIL]:
                    ArgusV4Error.GPS_ERRORS = 0
                    self.__turn_off_device(device_name)
                    return Errors.REBOOT_DEVICE
            else:
                ArgusV4Error.ASIL_ERRORS[ASIL] += 1
                if ArgusV4Error.ASIL_ERRORS[ASIL] >= ArgusV4Error.ASIL_THRESHOLDS[ASIL]:
                    ArgusV4Error.ASIL_ERRORS[ASIL] = 0
                    if device_cls.peripheral_line:
                        return Errors.GRACEFUL_REBOOT
                    else:
                        self.__turn_off_device(device_name)
                        return Errors.REBOOT_DEVICE
        return Errors.NO_REBOOT

    def graceful_reboot(self):
        """gracefully reboot: Gracefully reboot the device."""
        self.__turn_off_device("IMU")  # can be any device on peripheral line
        time.sleep(0.5)
        self.__turn_on_device("IMU")  # can be any device on peripheral line
        time.sleep(0.5)

    def turn_on_device(self, device_name: str):
        """turn_on_device: Turn on the device."""
        if device_name not in self.__device_list:
            return Errors.INVALID_DEVICE_NAME
        self.__turn_on_device(device_name)

    def reboot(self):
        """Reboot the satellite by resetting the main power."""
        ArgusV4Power.MAIN_PWR_RESET.value = True


class ArgusV4Error:
    ASIL_ERRORS = {
        ASIL1: 0,
        ASIL2: 0,
        ASIL3: 0,
    }

    ASIL_THRESHOLDS = {
        ASIL1: const(5),  # ASIL 1: Reboot after 5 errors
        ASIL2: const(3),  # ASIL 2: Reboot after 3 errors
        ASIL3: const(2),  # ASIL 3: Reboot after 2 errors
    }

    TORQUE_ERRORS = {
        "TORQUE_XP": 0,
        "TORQUE_XM": 0,
        "TORQUE_YP": 0,
        "TORQUE_YM": 0,
        "TORQUE_ZP": 0,
        "TORQUE_ZM": 0,
    }

    GPS_ERRORS = 0

    MAX_DEVICE_ERROR = const(10)
