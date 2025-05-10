"""
Author: Harry, Thomas, Ibrahima, Perrin
Description: This file contains the definition of the ArgusV1 class and its associated interfaces and components.
"""

from sys import path

import board
import neopixel
from busio import I2C, SPI, UART
from hal.cubesat import CubeSat
from hal.drivers.errors import Errors
from micropython import const
from sdcardio import SDCard
from storage import VfsFat, mount


class ArgusV1Interfaces:
    """
    This class represents the interfaces used in the ArgusV1 module.
    """

    I2C1_SDA = board.SDA1  # PB12
    I2C1_SCL = board.SCL1  # PB13

    # Line may not be connected, try except sequence
    try:
        I2C1 = I2C(I2C1_SCL, I2C1_SDA)
    except Exception as e:
        print(e)
        I2C1 = None

    I2C2_SDA = board.SDA2  # PA22
    I2C2_SCL = board.SCL2  # PA23

    # Line may not be connected, try except sequence
    try:
        I2C2 = I2C(I2C2_SCL, I2C2_SDA)
    except Exception as e:
        print(e)
        I2C2 = None

    I2C3_SDA = board.SDA3  # PA16
    I2C3_SCL = board.SCL3  # PA17

    # Line may not be connected, try except sequence
    try:
        I2C3 = I2C(I2C3_SCL, I2C3_SDA)
    except Exception as e:
        print(e)
        I2C3 = None

    JET_SPI_SCK = board.JETSON_SCK  # PA5
    JET_SPI_MOSI = board.JETSON_MOSI  # PA4
    JET_SPI_MISO = board.JETSON_MISO  # PA6
    JET_SPI = SPI(JET_SPI_SCK, MOSI=JET_SPI_MOSI, MISO=JET_SPI_MISO)

    SPI_SCK = board.SCK  # PA13
    SPI_MOSI = board.MOSI  # PA12
    SPI_MISO = board.MISO  # PA14
    SPI = SPI(SPI_SCK, MOSI=SPI_MOSI, MISO=SPI_MISO)

    UART1_BAUD = const(9600)
    UART1_TX = board.TX  # PB2
    UART1_RX = board.RX  # PB3
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
    JETSON_POWER_MONITOR_I2C_ADDRESS = const(0x45)  # 8A

    # X TORQUE COILS
    TORQUE_COILS_X_I2C = ArgusV1Interfaces.I2C1
    TORQUE_XP_I2C_ADDRESS = const(0x64)
    TORQUE_XM_I2C_ADDRESS = const(0x63)

    # X COIL DRIVER POWER MONITOR
    TORQUE_X_POWER_MONITOR_I2C = ArgusV1Interfaces.I2C1
    TORQUE_XP_POWER_MONITOR_I2C_ADDRESS = const(0x42)  # 84
    TORQUE_XM_POWER_MONITOR_I2C_ADDRESS = const(0x40)  # 80

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
    TORQUE_YP_POWER_MONITOR_I2C_ADDRESS = const(0x42)  # 84
    TORQUE_YM_POWER_MONITOR_I2C_ADDRESS = const(0x40)  # 80

    # Y SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_Y_POWER_MONITOR_I2C = ArgusV1Interfaces.I2C2
    SOLAR_CHARGING_YP_POWER_MONITOR_I2C_ADDRESS = const(0x49)  # 92
    SOLAR_CHARGING_YM_POWER_MONITOR_I2C_ADDRESS = const(0x48)  # 90

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
    TORQUE_ZP_POWER_MONITOR_I2C_ADDRESS = const(0x42)  # 84
    TORQUE_ZM_POWER_MONITOR_I2C_ADDRESS = const(0x40)  # 80

    # ZP SOLAR CHARGING POWER MONITOR
    SOLAR_CHARGING_Z_POWER_MONITOR_I2C = ArgusV1Interfaces.I2C3
    SOLAR_CHARGING_ZP_POWER_MONITOR_I2C_ADDRESS = const(0x4A)  # 94

    # ZM LIGHT SENSOR
    LIGHT_SENSOR_Z_I2C = ArgusV1Interfaces.I2C3
    LIGHT_SENSOR_ZM_I2C_ADDRESS = const(0x44)  # Conflict with ZP

    # ZP SUN SENSOR
    SUN_SENSOR_ZP_I2C = ArgusV1Interfaces.I2C3
    LIGHT_SENSOR_ZP1_I2C_ADDRESS = const(0x44)  # Conflict with ZM
    LIGHT_SENSOR_ZP2_I2C_ADDRESS = const(0x45)
    LIGHT_SENSOR_ZP3_I2C_ADDRESS = const(0x46)
    LIGHT_SENSOR_ZP4_I2C_ADDRESS = const(0x47)

    # GPS
    GPS_UART = ArgusV1Interfaces.UART1
    GPS_ENABLE = board.GPS_EN  # PB1

    # RADIO
    RADIO_SPI = ArgusV1Interfaces.SPI
    # RADIO_CS = board.RF1_CS
    # RADIO_RESET = board.RF1_RST
    # RADIO_ENABLE = board.EN_RF
    # RADIO_DIO0 = board.RF1_IO0
    # RADIO_FREQ = 915.6

    # SD CARD
    SD_CARD_SPI = ArgusV1Interfaces.SPI
    SD_CARD_CS = board.SD_CS  # PA27
    SD_BAUD = const(4000000)  # 4 MHz

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

    def __init__(self, debug: bool = False):
        """__init__: Initializes the Argus V1 CubeSat."""
        self.__debug = debug

        super().__init__()
        self.append_device("NEOPIXEL", self.__neopixel_boot)

    ######################## BOOT SEQUENCE ########################

    def boot_sequence(self) -> list[int]:
        """boot_sequence: Boot sequence for the CubeSat."""

        for name, device in self.__device_list.items():
            func = device.boot_fn
            device.device, device.error = func(name)

    def __gps_boot(self, _) -> list[int]:
        """GPS_boot: Boot sequence for the GPS

        :return: Error code if the GPS failed to initialize
        """
        try:
            from hal.drivers.gps import GPS

            gps = GPS(ArgusV1Components.GPS_UART, ArgusV1Components.GPS_ENABLE)

            return [gps, Errors.NO_ERROR]
        except Exception as e:
            if self.__debug:
                raise e

            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __power_monitor_boot(self, location) -> list[int]:
        """power_monitor_boot: Boot sequence for the power monitor

        :return: Error code if the power monitor failed to initialize
        """

        from hal.drivers.adm1176 import ADM1176

        locations = {
            "BOARD_PWR": [ArgusV1Components.BOARD_POWER_MONITOR_I2C_ADDRESS, ArgusV1Components.BOARD_POWER_MONITOR_I2C],
            "JETSON_PWR": [ArgusV1Components.JETSON_POWER_MONITOR_I2C_ADDRESS, ArgusV1Components.JETSON_POWER_MONITOR_I2C],
            "XP_PWR": [
                ArgusV1Components.SOLAR_CHARGING_XP_POWER_MONITOR_I2C_ADDRESS,
                ArgusV1Components.SOLAR_CHARGING_X_POWER_MONITOR_I2C,
            ],
            "XM_PWR": [
                ArgusV1Components.SOLAR_CHARGING_XM_POWER_MONITOR_I2C_ADDRESS,
                ArgusV1Components.SOLAR_CHARGING_X_POWER_MONITOR_I2C,
            ],
            "YP_PWR": [
                ArgusV1Components.SOLAR_CHARGING_YP_POWER_MONITOR_I2C_ADDRESS,
                ArgusV1Components.SOLAR_CHARGING_Y_POWER_MONITOR_I2C,
            ],
            "YM_PWR": [
                ArgusV1Components.SOLAR_CHARGING_YM_POWER_MONITOR_I2C_ADDRESS,
                ArgusV1Components.SOLAR_CHARGING_Y_POWER_MONITOR_I2C,
            ],
            "ZP_PWR": [
                ArgusV1Components.SOLAR_CHARGING_ZP_POWER_MONITOR_I2C_ADDRESS,
                ArgusV1Components.SOLAR_CHARGING_Z_POWER_MONITOR_I2C,
            ],
        }
        data = locations[location]
        try:
            address = data[0]
            bus = data[1]
            power_monitor = ADM1176(bus, address)

            return [power_monitor, Errors.NO_ERROR]

        except Exception as e:
            print(f"Failed to initialize {location}: {e}")
            if self.__debug:
                raise e
            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __imu_boot(self, _) -> list[int]:
        """imu_boot: Boot sequence for the IMU

        :return: Error code if the IMU failed to initialize
        """
        try:
            from hal.drivers.bmx160 import BMX160

            imu = BMX160(
                ArgusV1Components.IMU_I2C,
                ArgusV1Components.IMU_I2C_ADDRESS,
            )

            return [imu, Errors.NO_ERROR]
        except Exception as e:
            print(f"Failed to initialize IMU: {e}")
            if self.__debug:
                raise e
            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __torque_drivers_boot(self, direction) -> list[int]:
        """Boot sequence for all torque drivers in predefined directions.

        :return: List of error codes for each torque driver in the order of directions
        """
        directions = {
            "TORQUE_XP": [ArgusV1Components.TORQUE_XP_I2C_ADDRESS, ArgusV1Components.TORQUE_COILS_X_I2C],
            "TORQUE_XM": [ArgusV1Components.TORQUE_XM_I2C_ADDRESS, ArgusV1Components.TORQUE_COILS_X_I2C],
            "TORQUE_YP": [ArgusV1Components.TORQUE_YP_I2C_ADDRESS, ArgusV1Components.TORQUE_COILS_Y_I2C],
            "TORQUE_YM": [ArgusV1Components.TORQUE_YM_I2C_ADDRESS, ArgusV1Components.TORQUE_COILS_Y_I2C],
            "TORQUE_ZP": [ArgusV1Components.TORQUE_ZP_I2C_ADDRESS, ArgusV1Components.TORQUE_COILS_Z_I2C],
            "TORQUE_ZM": [ArgusV1Components.TORQUE_ZM_I2C_ADDRESS, ArgusV1Components.TORQUE_COILS_Z_I2C],
        }

        from hal.drivers.drv8830 import DRV8830

        data = directions[direction]

        try:
            address = data[0]
            bus = data[1]
            torque_driver = DRV8830(bus, address)

            return [torque_driver, Errors.NO_ERROR]

        except Exception as e:
            if self.__debug:
                print(f"Failed to initialize {direction} torque driver: {e}")
                raise e
            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __light_sensors_boot(self, direction) -> list[int]:
        """Boot sequence for all light sensors in predefined directions.

        :return: List of error codes for each sensor in the order of directions
        """
        directions = {
            "LIGHT_XP": [ArgusV1Components.LIGHT_SENSOR_XP_I2C_ADDRESS, ArgusV1Components.LIGHT_SENSOR_X_I2C],
            "LIGHT_XM": [ArgusV1Components.LIGHT_SENSOR_XM_I2C_ADDRESS, ArgusV1Components.LIGHT_SENSOR_X_I2C],
            "LIGHT_YP": [ArgusV1Components.LIGHT_SENSOR_YP_I2C_ADDRESS, ArgusV1Components.LIGHT_SENSOR_Y_I2C],
            "LIGHT_YM": [ArgusV1Components.LIGHT_SENSOR_YM_I2C_ADDRESS, ArgusV1Components.LIGHT_SENSOR_Y_I2C],
            "LIGHT_ZM": [ArgusV1Components.LIGHT_SENSOR_ZM_I2C_ADDRESS, ArgusV1Components.LIGHT_SENSOR_Z_I2C],
            "LIGHT_ZP_1": [ArgusV1Components.LIGHT_SENSOR_ZP1_I2C_ADDRESS, ArgusV1Components.SUN_SENSOR_ZP_I2C],
            "LIGHT_ZP_2": [ArgusV1Components.LIGHT_SENSOR_ZP2_I2C_ADDRESS, ArgusV1Components.SUN_SENSOR_ZP_I2C],
            "LIGHT_ZP_3": [ArgusV1Components.LIGHT_SENSOR_ZP3_I2C_ADDRESS, ArgusV1Components.SUN_SENSOR_ZP_I2C],
            "LIGHT_ZP_4": [ArgusV1Components.LIGHT_SENSOR_ZP4_I2C_ADDRESS, ArgusV1Components.SUN_SENSOR_ZP_I2C],
        }

        from hal.drivers.opt4001 import OPT4001

        data = directions[direction]

        try:
            address = data[0]
            bus = data[1]
            light_sensor = OPT4001(
                bus,
                address,
                conversion_time=ArgusV1Components.LIGHT_SENSOR_CONVERSION_TIME,
            )
            return [light_sensor, Errors.NO_ERROR]

        except Exception as e:
            if self.__debug:
                print(f"Failed to initialize {direction} light sensor: {e}")
                raise e
            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __radio_boot(self, _) -> list[int]:
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

            return [radio, Errors.NO_ERROR]
        except Exception as e:
            if self.__debug:
                raise e

            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __rtc_boot(self, _) -> list[int]:
        """rtc_boot: Boot sequence for the RTC

        :return: Error code if the RTC failed to initialize
        """

        from hal.drivers.pcf8523 import PCF8523

        try:
            rtc = PCF8523(ArgusV1Components.RTC_I2C, ArgusV1Components.RTC_I2C_ADDRESS)
            return [rtc, Errors.NO_ERROR]
        except Exception as e:
            if self.__debug:
                raise e

            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __neopixel_boot(self) -> list[int]:
        """neopixel_boot: Boot sequence for the neopixel"""
        try:
            np = neopixel.NeoPixel(
                ArgusV1Components.NEOPIXEL_SDA,
                ArgusV1Components.NEOPIXEL_N,
                brightness=ArgusV1Components.NEOPIXEL_BRIGHTNESS,
                pixel_order=neopixel.GRB,
            )
            return [np, Errors.NO_ERROR]
        except Exception as e:
            if self.__debug:
                raise e

            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __sd_card_boot(self, _) -> list[object, int]:
        """sd_card_boot: Boot sequence for the SD card"""
        try:
            sd_card = SDCard(
                ArgusV1Components.SD_CARD_SPI,
                ArgusV1Components.SD_CARD_CS,
                ArgusV1Components.SD_BAUD,
            )

            vfs = VfsFat(sd_card)
            mount(vfs, ArgusV1Components.VFS_MOUNT_POINT)
            path.append(ArgusV1Components.VFS_MOUNT_POINT)
            return [vfs, Errors.NO_ERROR]
        except Exception as e:
            if self.__debug:
                raise e

            return [None, Errors.DEVICE_NOT_INITIALISED]

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

            return [burn_wires, Errors.NO_ERROR]
        except Exception as e:
            if self.__debug:
                raise e

            return [None, Errors.DEVICE_NOT_INITIALISED]

    def __fuel_gauge_boot(self) -> list[int]:
        """fuel_gauge_boot: Boot sequence for the fuel gauge"""
        try:
            from hal.drivers.max17205 import MAX17205

            fuel_gauge = MAX17205(
                ArgusV1Components.FUEL_GAUGE_I2C,
                ArgusV1Components.FUEL_GAUGE_I2C_ADDRESS,
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

    ######################## ERROR HANDLING ########################

    def handle_error(self, _: str) -> int:
        return Errors.NO_REBOOT

    def graceful_reboot_devices(self, device_name):
        pass

    def reboot(self):
        import supervisor

        supervisor.reload()
