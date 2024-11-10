"""
Author: Harry, Thomas, Ibrahima, Perrin
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
    SUN_SENSOR_ZP1_I2C_ADDRESS = const(0x44)  # Conflict with ZM
    SUN_SENSOR_ZP2_I2C_ADDRESS = const(0x45)
    SUN_SENSOR_ZP3_I2C_ADDRESS = const(0x46)
    SUN_SENSOR_ZP4_I2C_ADDRESS = const(0x47)

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
        error_list.append(self.__power_monitor_boot())
        error_list.append(self.__charger_boot())
        # error_list.append(self.__torque_drivers_boot())
        # error_list.append(self.__light_sensors_boot())  # light + sun sensors
        # error_list.append(self.__radio_boot())
        error_list.append(self.__neopixel_boot())
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

            gps1 = GPS(ArgusV1Components.GPS_UART, ArgusV1Components.GPS_ENABLE)

            if self.__middleware_enabled:
                gps1 = Middleware(gps1)

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
            "BOARD": [ArgusV1Components.BOARD_POWER_MONITOR_I2C_ADDRESS, ArgusV1Components.BOARD_POWER_MONITOR_I2C],
            # "JETSON": [ArgusV1Components.JETSON_POWER_MONITOR_I2C_ADDRESS, ArgusV1Components.JETSON_POWER_MONITOR_I2C],
            # "TORQUE_XP": [
            #     ArgusV1Components.TORQUE_XP_POWER_MONITOR_I2C_ADDRESS,
            #     ArgusV1Components.TORQUE_X_POWER_MONITOR_I2C,
            # ],
            # "TORQUE_XM": [
            #     ArgusV1Components.TORQUE_XM_POWER_MONITOR_I2C_ADDRESS,
            #     ArgusV1Components.TORQUE_X_POWER_MONITOR_I2C,
            # ],
            # "TORQUE_YP": [
            #     ArgusV1Components.TORQUE_YP_POWER_MONITOR_I2C_ADDRESS,
            #     ArgusV1Components.TORQUE_Y_POWER_MONITOR_I2C,
            # ],
            # "TORQUE_YM": [
            #     ArgusV1Components.TORQUE_YM_POWER_MONITOR_I2C_ADDRESS,
            #     ArgusV1Components.TORQUE_Y_POWER_MONITOR_I2C,
            # ],
            # "TORQUE_ZP": [
            #     ArgusV1Components.TORQUE_ZP_POWER_MONITOR_I2C_ADDRESS,
            #     ArgusV1Components.TORQUE_Z_POWER_MONITOR_I2C,
            # ],
            # "TORQUE_ZM": [
            #     ArgusV1Components.TORQUE_ZM_POWER_MONITOR_I2C_ADDRESS,
            #     ArgusV1Components.TORQUE_Z_POWER_MONITOR_I2C,
            # ],
            # "SOLAR_XP": [
            #     ArgusV1Components.SOLAR_CHARGING_XP_POWER_MONITOR_I2C_ADDRESS,
            #     ArgusV1Components.SOLAR_CHARGING_X_POWER_MONITOR_I2C,
            # ],
            # "SOLAR_XM": [
            #     ArgusV1Components.SOLAR_CHARGING_XM_POWER_MONITOR_I2C_ADDRESS,
            #     ArgusV1Components.SOLAR_CHARGING_X_POWER_MONITOR_I2C,
            # ],
            # "SOLAR_YP": [
            #     ArgusV1Components.SOLAR_CHARGING_YP_POWER_MONITOR_I2C_ADDRESS,
            #     ArgusV1Components.SOLAR_CHARGING_Y_POWER_MONITOR_I2C,
            # ],
            # "SOLAR_YM": [
            #     ArgusV1Components.SOLAR_CHARGING_YM_POWER_MONITOR_I2C_ADDRESS,
            #     ArgusV1Components.SOLAR_CHARGING_Y_POWER_MONITOR_I2C,
            # ],
            # "SOLAR_ZP": [
            #     ArgusV1Components.SOLAR_CHARGING_ZP_POWER_MONITOR_I2C_ADDRESS,
            #     ArgusV1Components.SOLAR_CHARGING_Z_POWER_MONITOR_I2C,
            # ],
        }

        from hal.drivers.adm1176 import ADM1176

        error_codes = []

        for location, busAndAddress in locations.items():
            try:
                address = busAndAddress[0]
                bus = busAndAddress[1]
                power_monitor = ADM1176(bus, address)

                if self.__middleware_enabled:
                    power_monitor = Middleware(power_monitor)

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
            from hal.drivers.bmx160 import BMX160

            imu = BMX160(
                ArgusV1Components.IMU_I2C,
                ArgusV1Components.IMU_I2C_ADDRESS,
            )

            if self.__middleware_enabled:
                imu = Middleware(imu)

            self.__imu = imu
            self.__imu_name = "BMX160"
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

    def __torque_drivers_boot(self) -> list[int]:
        """Boot sequence for all torque drivers in predefined directions.

        :return: List of error codes for each torque driver in the order of directions
        """
        directions = {
            "XP": [ArgusV1Components.TORQUE_XP_I2C_ADDRESS, ArgusV1Components.TORQUE_COILS_X_I2C],
            "XM": [ArgusV1Components.TORQUE_XM_I2C_ADDRESS, ArgusV1Components.TORQUE_COILS_X_I2C],
            "YP": [ArgusV1Components.TORQUE_YP_I2C_ADDRESS, ArgusV1Components.TORQUE_COILS_Y_I2C],
            "YM": [ArgusV1Components.TORQUE_YM_I2C_ADDRESS, ArgusV1Components.TORQUE_COILS_Y_I2C],
            "ZP": [ArgusV1Components.TORQUE_ZP_I2C_ADDRESS, ArgusV1Components.TORQUE_COILS_Z_I2C],
            "ZM": [ArgusV1Components.TORQUE_ZM_I2C_ADDRESS, ArgusV1Components.TORQUE_COILS_Z_I2C],
        }

        from hal.drivers.drv8830 import DRV8830

        error_codes = []

        for direction, busAndAddress in directions.items():
            try:
                address = busAndAddress[0]
                bus = busAndAddress[1]
                torque_driver = DRV8830(bus, address)

                if self.__middleware_enabled:
                    torque_driver = Middleware(torque_driver)

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
            "XP": [ArgusV1Components.LIGHT_SENSOR_XP_I2C_ADDRESS, ArgusV1Components.LIGHT_SENSOR_X_I2C],
            "XM": [ArgusV1Components.LIGHT_SENSOR_XM_I2C_ADDRESS, ArgusV1Components.LIGHT_SENSOR_X_I2C],
            "YP": [ArgusV1Components.LIGHT_SENSOR_YP_I2C_ADDRESS, ArgusV1Components.LIGHT_SENSOR_Y_I2C],
            "YM": [ArgusV1Components.LIGHT_SENSOR_YM_I2C_ADDRESS, ArgusV1Components.LIGHT_SENSOR_Y_I2C],
            "ZM": [ArgusV1Components.LIGHT_SENSOR_ZM_I2C_ADDRESS, ArgusV1Components.LIGHT_SENSOR_Z_I2C],
            "ZP1": [ArgusV1Components.SUN_SENSOR_ZP1_I2C_ADDRESS, ArgusV1Components.SUN_SENSOR_ZP_I2C],
            "ZP2": [ArgusV1Components.SUN_SENSOR_ZP2_I2C_ADDRESS, ArgusV1Components.SUN_SENSOR_ZP_I2C],
            "ZP3": [ArgusV1Components.SUN_SENSOR_ZP3_I2C_ADDRESS, ArgusV1Components.SUN_SENSOR_ZP_I2C],
            "ZP4": [ArgusV1Components.SUN_SENSOR_ZP4_I2C_ADDRESS, ArgusV1Components.SUN_SENSOR_ZP_I2C],
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
                    conversion_time=ArgusV1Components.LIGHT_SENSOR_CONVERSION_TIME,
                )

                if self.__middleware_enabled:
                    light_sensor = Middleware(light_sensor)

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

            rtc = PCF8523(ArgusV1Components.RTC_I2C, ArgusV1Components.RTC_I2C_ADDRESS)

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
