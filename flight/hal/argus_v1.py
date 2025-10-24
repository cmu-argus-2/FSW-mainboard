"""
Author: Harry, Thomas, Ibrahima
Description: This file contains the definition of the ArgusV1 class and its associated interfaces and components.
"""

import gc
from sys import path

import board
from busio import I2C, SPI, UART
from hal.cubesat import CubeSat
from hal.drivers.errors import Errors
from micropython import const


class ArgusV1Interfaces:
    """
    This class represents the interfaces used in the Argus V1 board.
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

    This class defines constants for various components such as GPS, board power monitor,
    Jetson power monitor, IMU, charger, torque coils, light sensors, radio, and SD card.
    """

    # GPS
    GPS_UART = ArgusV1Interfaces.UART1
    GPS_ENABLE = board.EN_GPS

    # BOARD POWER MONITOR
    BOARD_POWER_MONITOR_I2C = ArgusV1Interfaces.I2C1
    BOARD_POWER_MONITOR_I2C_ADDRESS = const(0x4A)

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
    RADIO_FREQ = 915.6

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

    # PAYLOAD
    PAYLOAD_UART = ArgusV1Interfaces.UART2
    PAYLOAD_ENABLE = board.EN_JET

    # VFS
    VFS_MOUNT_POINT = "/sd"


class ArgusV1(CubeSat):
    """ArgusV1: Represents the Argus V1 CubeSat."""

    __slots__ = "__debug"

    def __init__(self, debug: bool = False):
        """__init__: Initializes the Argus V1 CubeSat."""
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
        error_list.append(self.__imu_boot())  # 4% of RAM
        error_list.append(self.__rtc_boot())
        error_list.append(self.__gps_boot())
        error_list.append(self.__board_power_monitor_boot())
        error_list.append(self.__jetson_power_monitor_boot())
        error_list.append(self.__charger_boot())
        error_list.append(self.__torque_drivers_boot())
        error_list.append(self.__light_sensors_boot())
        error_list.append(self.__radio_boot())
        error_list.append(self.__burn_wire_boot())
        error_list.append(self.__payload_uart_boot())

        gc.collect()

        error_list = [error for error in error_list if error != Errors.NO_ERROR]

        if self.__debug:
            print("Boot Errors:")
            print()
            for error in error_list:
                print(f"{Errors.diagnostic_to_string(error)}")
            print()

        self.__recent_errors = error_list

        return error_list

    def __gps_boot(self) -> list[int]:
        """GPS_boot: Boot sequence for the GPS

        :return: Error code if the GPS failed to initialize
        """
        try:
            from hal.drivers.gps import GPS

            gps1 = GPS(ArgusV1Components.GPS_UART, ArgusV1Components.GPS_ENABLE)

            self.__gps = gps1
            self.__device_list.append(gps1)
        except Exception as e:
            self.__gps = None
            if self.__debug:
                raise e

            return Errors.GPS_NOT_INITIALIZED

        return Errors.NO_ERROR

    def __board_power_monitor_boot(self) -> list[int]:
        """board_power_monitor_boot: Boot sequence for the board power monitor

        :return: Error code if the board power monitor failed to initialize
        """
        try:
            from hal.drivers.adm1176 import ADM1176

            board_monitor = ADM1176(
                ArgusV1Components.BOARD_POWER_MONITOR_I2C,
                ArgusV1Components.BOARD_POWER_MONITOR_I2C_ADDRESS,
            )

            self.__board_monitor = board_monitor
            self.__device_list.append(board_monitor)
        except Exception as e:
            self.__battery_monitor = None
            print(e)
            if self.__debug:
                raise e

            return Errors.DEVICE_NOT_INITIALISED

        return Errors.NO_ERROR

    def __jetson_power_monitor_boot(self) -> list[int]:
        """jetson_power_monitor_boot: Boot sequence for the Jetson power monitor

        :return: Error code if the Jetson power monitor failed to initialize
        """
        try:
            from hal.drivers.adm1176 import ADM1176

            jetson_power_monitor = ADM1176(
                ArgusV1Components.JETSON_POWER_MONITOR_I2C,
                ArgusV1Components.JETSON_POWER_MONITOR_I2C_ADDRESS,
            )

            self.__jetson_power_monitor = jetson_power_monitor
            self.__device_list.append(jetson_power_monitor)
        except Exception as e:
            self.__jetson_power_monitor = None
            if self.__debug:
                raise e

            return Errors.DEVICE_NOT_INITIALISED

        return Errors.NO_ERROR

    def __imu_boot(self) -> list[int]:
        """imu_boot: Boot sequence for the IMU

        :return: Error code if the IMU failed to initialize
        """
        try:
            from hal.drivers.bmx160 import BMX160

            imu = BMX160(
                ArgusV1Components.IMU_I2C,
                ArgusV1Components.IMU_I2C_ADDRESS,
                ArgusV1Components.IMU_ENABLE,
            )

            self.__imu = imu
            self.__imu_temp_flag = True
            self.__device_list.append(imu)
        except Exception as e:
            self.__imu = None
            if self.__debug:
                raise e

            return Errors.DEVICE_NOT_INITIALISED

        return Errors.NO_ERROR

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

            self.__charger = charger
            self.__device_list.append(charger)
        except Exception as e:
            self.__charger = None
            if self.__debug:
                raise e

            return Errors.DEVICE_NOT_INITIALISED

        return Errors.NO_ERROR

    def __torque_drivers_boot(self) -> list[int]:
        """Boot sequence for all torque drivers in predefined directions.

        :return: List of error codes for each torque driver in the order of directions
        """
        directions = {
            "XP": ArgusV1Components.TORQUE_XP_I2C_ADDRESS,
            "XM": ArgusV1Components.TORQUE_XM_I2C_ADDRESS,
            "YP": ArgusV1Components.TORQUE_YP_I2C_ADDRESS,
            "YM": ArgusV1Components.TORQUE_YM_I2C_ADDRESS,
            "Z": ArgusV1Components.TORQUE_Z_I2C_ADDRESS,
        }

        from hal.drivers.drv8830 import DRV8830

        error_codes = []

        for direction, address in directions.items():
            try:
                torque_driver = DRV8830(
                    ArgusV1Components.TORQUE_COILS_I2C,
                    address,
                )

                self.__torque_drivers[direction] = torque_driver
                self.__device_list.append(torque_driver)
                error_codes.append(Errors.NO_ERROR)  # Append success code if no error

            except Exception as e:
                self.__torque_drivers[direction] = None
                if self.__debug:
                    print(f"Failed to initialize {direction} torque driver: {e}")
                    raise e
                error_codes.append(Errors.DEVICE_NOT_INITIALISED)  # Append failure code

        return error_codes

    def __light_sensors_boot(self) -> list[int]:
        """Boot sequence for all light sensors in predefined directions.

        :return: List of error codes for each sensor in the order of directions
        """
        directions = {
            "XP": ArgusV1Components.LIGHT_SENSOR_XP_I2C_ADDRESS,
            "XM": ArgusV1Components.LIGHT_SENSOR_XM_I2C_ADDRESS,
            "YP": ArgusV1Components.LIGHT_SENSOR_YP_I2C_ADDRESS,
            "YM": ArgusV1Components.LIGHT_SENSOR_YM_I2C_ADDRESS,
            "ZM": ArgusV1Components.LIGHT_SENSOR_ZM_I2C_ADDRESS,
        }

        from hal.drivers.opt4001 import OPT4001

        error_codes = []  # List to store error codes per sensor

        for direction, address in directions.items():
            try:
                light_sensor = OPT4001(
                    ArgusV1Components.LIGHT_SENSORS_I2C,
                    address,
                    conversion_time=ArgusV1Components.LIGHT_SENSOR_CONVERSION_TIME,
                )

                self.__light_sensors[direction] = light_sensor
                self.__device_list.append(light_sensor)
                error_codes.append(Errors.NO_ERROR)  # Append success code if no error

            except Exception as e:
                self.__light_sensors[direction] = None
                if self.__debug:
                    print(f"Failed to initialize {direction} light sensor: {e}")
                    raise e
                error_codes.append(Errors.DEVICE_NOT_INITIALISED)  # Append failure code

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

            self.__radio = radio
            self.__device_list.append(radio)
        except Exception as e:
            self.__radio = None
            if self.__debug:
                raise e

            return Errors.RFM9X_NOT_INITIALIZED

        return Errors.NO_ERROR

    def __rtc_boot(self) -> list[int]:
        """rtc_boot: Boot sequence for the RTC

        :return: Error code if the RTC failed to initialize
        """
        try:
            from hal.drivers.pcf8523 import PCF8523

            rtc = PCF8523(ArgusV1Components.RTC_I2C, ArgusV1Components.RTC_I2C_ADDRESS)

            self.__rtc = rtc
            self.__device_list.append(rtc)
        except Exception as e:
            self.__rtc = None
            if self.__debug:
                raise e

            return Errors.DEVICE_NOT_INITIALISED

        return Errors.NO_ERROR

    def __sd_card_boot(self) -> list[int]:
        """sd_card_boot: Boot sequence for the SD card"""
        try:
            from sdcardio import SDCard

            sd_card = SDCard(
                ArgusV1Components.SD_CARD_SPI,
                ArgusV1Components.SD_CARD_CS,
                ArgusV1Components.SD_BAUD,
            )
            self.__sd_card = sd_card
            self.append_device(sd_card)
        except Exception as e:
            self.__sd_card = None
            if self.__debug:
                raise e

            return Errors.DEVICE_NOT_INITIALISED

        return Errors.NO_ERROR

    def __vfs_boot(self) -> list[int]:
        """vfs_boot: Boot sequence for the VFS"""
        if self.__sd_card is None:
            return Errors.DEVICE_NOT_INITIALISED

        try:
            from storage import VfsFat, mount

            vfs = VfsFat(self.__sd_card)

            mount(vfs, ArgusV1Components.VFS_MOUNT_POINT)
            path.append(ArgusV1Components.VFS_MOUNT_POINT)

            path.append(ArgusV1Components.VFS_MOUNT_POINT)
            self.__vfs = vfs
        except Exception as e:
            self.__vfs = None
            if self.__debug:
                raise e
            raise e

            return Errors.DEVICE_NOT_INITIALISED

        return Errors.NO_ERROR

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

            self.__burn_wires = burn_wires
            self.append_device(burn_wires)
        except Exception as e:
            self.__burn_wires = None
            if self.__debug:
                raise e

            return Errors.DEVICE_NOT_INITIALISED

        return Errors.NO_ERROR

    def __payload_uart_boot(self) -> list[int]:
        """payload_uart_boot: Boot sequence for the Jetson UART"""
        try:
            from hal.drivers.payload import PayloadUART

            payload_uart = PayloadUART(
                ArgusV1Components.PAYLOAD_UART,
                ArgusV1Components.PAYLOAD_ENABLE,
            )

            self.__payload_uart = payload_uart
            self.__device_list.append(self.__payload_uart)
        except Exception as e:
            self.__payload_uart = None
            if self.__debug:
                raise e

            return Errors.DEVICE_NOT_INITIALISED

        return Errors.NO_ERROR

    ######################## INTERFACES ########################
    def APPLY_MAGNETIC_CONTROL(self, ctrl) -> None:
        """CONTROL_COILS: Control the coils on the CubeSat, depending on the control mode (identical for all coils)."""
        # TODO error handlling
        for direction, value in ctrl.items():
            if direction in self.__torque_drivers:
                self.__torque_drivers[direction].set_throttle_volts(value)

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
