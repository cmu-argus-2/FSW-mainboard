"""
CircuitPython driver for the modified PyCubed satellite board
PyCubed Hardware Version: mainboard-v05
CircuitPython Version: 7.0.0 alpha
"""

import sys
import time

# Common CircuitPython Libs
import board
import busio
import digitalio
import microcontroller
import neopixel  # RGB LED
import pwmio
import sdcardio
from analogio import AnalogIn
from micropython import const
from storage import VfsFat, mount, umount

# Hardware Specific Libs
from .drivers_PYC_V05 import adm1176  # Power Monitor
from .drivers_PYC_V05 import bmx160  # IMU
from .drivers_PYC_V05 import bq25883  # USB Charger
from .drivers_PYC_V05 import rfm9x  # Radio

# Common CircuitPython Libs
from .drivers_PYC_V05.bitflags import bitFlag, multiBitFlag

# NVM register numbers
_BOOTCNT = const(0)
_VBUSRST = const(6)
_STATECNT = const(7)
_TOUTS = const(9)
_GSRSP = const(10)
_ICHRG = const(11)
_FLAG = const(16)

SEND_BUFF = bytearray(252)


class device:
    """
    Based on the code from: https://docs.python.org/3/howto/descriptor.html#properties
    Attempts to return the appropriate hardware device.
    If this fails, it will attempt to reinitialize the hardware.
    If this fails again, it will raise an exception.
    """

    def __init__(self, fget=None):
        self.fget = fget
        self._device = None

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        if self.fget is None:
            raise AttributeError(f"unreadable attribute {self._name}")

        if self._device is not None:
            return self._device
        else:
            self._device = self.fget(instance)
            return self._device


class PyCubed:
    # General NVM counters
    c_boot = multiBitFlag(register=_BOOTCNT, lowest_bit=0, num_bits=8)
    c_vbusrst = multiBitFlag(register=_VBUSRST, lowest_bit=0, num_bits=8)
    c_state_err = multiBitFlag(register=_STATECNT, lowest_bit=0, num_bits=8)
    c_gs_resp = multiBitFlag(register=_GSRSP, lowest_bit=0, num_bits=8)
    c_ichrg = multiBitFlag(register=_ICHRG, lowest_bit=0, num_bits=8)

    # Define NVM flags
    f_lowbatt = bitFlag(register=_FLAG, bit=0)
    f_solar = bitFlag(register=_FLAG, bit=1)
    f_gpson = bitFlag(register=_FLAG, bit=2)
    f_lowbtout = bitFlag(register=_FLAG, bit=3)
    f_gpsfix = bitFlag(register=_FLAG, bit=4)
    f_shtdwn = bitFlag(register=_FLAG, bit=5)

    instance = None

    def __new__(cls):
        """
        Override to ensure this class has only one instance.
        """
        if not cls.instance:
            cls.instance = object.__new__(cls)
            cls.instance = super(PyCubed, cls).__new__(cls)
        return cls.instance

    def __init__(self):  # noqa: C901
        """
        Big init routine as the whole board is brought up.
        """
        self.BOOTTIME = const(time.monotonic())
        self.data_cache = {}
        self.filenumbers = {}
        self.vlowbatt = 6.0
        self.send_buff = memoryview(SEND_BUFF)
        self.debug = True
        self.micro = microcontroller
        self.hardware = {
            "IMU": False,
            "Radio1": False,
            "Radio2": False,
            "SDcard": False,
            "GPS": False,
            "WDT": False,
            "USB": False,
            "PWR": False,
        }
        # Define burn wires:
        self._relayA = digitalio.DigitalInOut(board.RELAY_A)
        self._relayA.switch_to_output(drive_mode=digitalio.DriveMode.OPEN_DRAIN)
        self._resetReg = digitalio.DigitalInOut(board.VBUS_RST)
        self._resetReg.switch_to_output(drive_mode=digitalio.DriveMode.OPEN_DRAIN)

        # Define battery voltage
        self._vbatt = AnalogIn(board.BATTERY)

        # Define MPPT charge current measurement
        self._ichrg = AnalogIn(board.L1PROG)
        self._chrg = digitalio.DigitalInOut(board.CHRG)
        self._chrg.switch_to_input()

        # Define SPI,I2C,UART
        self.i2c1 = busio.I2C(board.SCL, board.SDA)
        self.spi = board.SPI()
        self.uart = busio.UART(board.TX, board.RX)

        # Define GPS
        self.en_gps = digitalio.DigitalInOut(board.EN_GPS)
        self.en_gps.switch_to_output()

        # Define radio
        _rf_cs1 = digitalio.DigitalInOut(board.RF1_CS)
        _rf_rst1 = digitalio.DigitalInOut(board.RF1_RST)
        self.enable_rf = digitalio.DigitalInOut(board.EN_RF)
        self.RADIO_DIO0 = digitalio.DigitalInOut(board.RF1_IO0)
        # self.enable_rf.switch_to_output(value=False) # if U21
        self.enable_rf.switch_to_output(value=True)  # if U7
        _rf_cs1.switch_to_output(value=True)
        _rf_rst1.switch_to_output(value=True)
        self.RADIO_DIO0.switch_to_input()

        # If the same SPI bus is shared with other peripherals,
        # the SD card must be initialized before accessing any other peripheral on the bus.
        # Failure to do so can prevent the SD card from being recognized until it is powered off or re-inserted.
        try:
            # Baud rate depends on the card, 4MHz should be safe
            _sd = sdcardio.SDCard(self.spi, board.SD_CS, baudrate=4000000)
            _vfs = VfsFat(_sd)
            mount(_vfs, "/sd")
            sys.path.append("/sd")
            self.fs = _vfs
            self.hardware["SDcard"] = True
        except Exception as e:
            if self.debug:
                print("[ERROR][SD Card]", e)

        # Initialize Neopixel
        try:
            self.neopixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2, pixel_order=neopixel.GRB)
            self.neopixel[0] = (0, 0, 0)
            self.hardware["Neopixel"] = True
        except Exception as e:
            if self.debug:
                print("[WARNING][Neopixel]", e)

        # Initialize USB charger
        try:
            self.usb = bq25883.BQ25883(self.i2c1)
            self.usb.charging = False
            self.usb.wdt = False
            self.usb.led = False
            self.usb.charging_current = 8  # 400mA
            self.usb_charging = False
            self.hardware["USB"] = True
        except Exception as e:
            if self.debug:
                print("[ERROR][USB Charger]", e)

        # Initialize Power Monitor
        try:
            self.pwr = adm1176.ADM1176(self.i2c1)
            self.pwr.sense_resistor = 0.1
            self.hardware["PWR"] = True
        except Exception as e:
            if self.debug:
                print("[ERROR][Power Monitor]", e)

        # Initialize IMU
        try:
            self.IMU = bmx160.BMX160_I2C(self.i2c1)
            self.hardware["IMU"] = True
        except Exception as e:
            if self.debug:
                print("[ERROR][IMU]", e)

        # # Initialize GPS
        # try:
        #     self.gps = GPS(self.uart,debug=False) # still powered off!
        #     self.gps.timeout_handler=self.timeout_handler
        #     self.hardware['GPS'] = True
        # except Exception as e:
        #     if self.debug: print('[ERROR][GPS]',e)

        # Initialize radio #1 - UHF
        try:
            self.RADIO = rfm9x.RFM9x(self.spi, _rf_cs1, _rf_rst1, 433, code_rate=8, baudrate=1320000)
            # Default LoRa Modulation Settings
            # Frequency: 433 MHz, SF7, BW125kHz, CR4/8, Preamble=8, CRC=True
            self.RADIO.dio0 = self.RADIO_DIO0
            self.RADIO.set_enable_crc(True)
            self.RADIO.ack_delay = 0.2
            self.RADIO.sleep()
            self.hardware["Radio1"] = True
        except Exception as e:
            if self.debug:
                print("[ERROR][RADIO 1]", e)

        # set PyCubed power mode
        self.power_mode = "normal"

    def reinit(self, dev):
        dev = dev.lower()
        if dev == "gps":
            self.gps.__init__(self.uart, debug=False)
        elif dev == "pwr":
            self.pwr.__init__(self.i2c1)
        elif dev == "usb":
            self.usb.__init__(self.i2c1)
        elif dev == "imu":
            self.IMU.__init__(self.i2c1)
        else:
            print("Invalid Device? ->", dev)

    @property
    def acceleration(self):
        if self.hardware["IMU"]:
            return self.IMU.accel  # m/s^2

    @property
    def magnetic(self):
        if self.hardware["IMU"]:
            return self.IMU.mag  # uT

    @property
    def gyro(self):
        if self.hardware["IMU"]:
            return self.IMU.gyro  # deg/s

    @property
    def temperature(self):
        if self.hardware["IMU"]:
            return self.IMU.temperature  # Celsius

    @property
    def RGB(self):
        return self.neopixel[0]

    @RGB.setter
    def RGB(self, value):
        if self.hardware["Neopixel"]:
            try:
                self.neopixel[0] = value
            except Exception as e:
                print("[WARNING]", e)

    @property
    def charge_batteries(self):
        if self.hardware["USB"]:
            return self.usb_charging

    @charge_batteries.setter
    def charge_batteries(self, value):
        if self.hardware["USB"]:
            self.usb_charging = value
            self.usb.led = value
            self.usb.charging = value

    @property
    def battery_voltage(self):
        _vbat = 0
        for _ in range(50):
            _vbat += self._vbatt.value * 3.3 / 65536
        _voltage = (_vbat / 50) * (316 + 110) / 110  # 316/110 voltage divider
        return _voltage  # volts

    @property
    def system_voltage(self):
        if self.hardware["PWR"]:
            try:
                return self.pwr.read()[0]  # volts
            except Exception as e:
                print("[WARNING][PWR Monitor]", e)
        else:
            print("[WARNING] Power monitor not initialized")

    @property
    def current_draw(self):
        """
        current draw from batteries
        NOT accurate if powered via USB
        """
        if self.hardware["PWR"]:
            idraw = 0
            try:
                for _ in range(50):  # average 50 readings
                    idraw += self.pwr.read()[1]
                return (idraw / 50) * 1000  # mA
            except Exception as e:
                print("[WARNING][PWR Monitor]", e)
        else:
            print("[WARNING] Power monitor not initialized")

    def charge_current(self):
        """
        LTC4121 solar charging IC with charge current monitoring
        See Programming the Charge Current section
        """
        _charge = 0
        if self.solar_charging:
            _charge = self._ichrg.value * 3.3 / 65536
            _charge = ((_charge * 988) / 3010) * 1000
        return _charge  # mA

    @property
    def solar_charging(self):
        return not self._chrg.value

    @property
    def reset_vbus(self):
        # unmount SD card to avoid errors
        if self.hardware["SDcard"]:
            try:
                umount("/sd")
                self.spi.deinit()
                time.sleep(3)
            except Exception as e:
                print("vbus reset error?", e)
                pass
        self._resetReg.drive_mode = digitalio.DriveMode.PUSH_PULL
        self._resetReg.value = 1

    def timeout_handler(self):
        print("Incrementing timeout register")
        if (self.micro.nvm[_TOUTS] + 1) >= 255:
            self.micro.nvm[_TOUTS] = 0
            # soft reset
            self.micro.on_next_reset(self.micro.RunMode.NORMAL)
            self.micro.reset()
        else:
            self.micro.nvm[_TOUTS] += 1

    def powermode(self, mode):
        """
        TODO
        Configure the hardware for minimum or normal power consumption
        Add custom modes for mission-specific control
        """
        if "min" in mode:
            self.RGB = (0, 0, 0)
            self.neopixel.brightness = 0
            if self.hardware["Radio1"]:
                self.RADIO.sleep()
            if self.hardware["Radio2"]:
                self.radio2.sleep()
            self.enable_rf.value = False
            if self.hardware["IMU"]:
                self.IMU.gyro_powermode = 0x14  # suspend mode
                self.IMU.accel_powermode = 0x10  # suspend mode
                self.IMU.mag_powermode = 0x18  # suspend mode
            if self.hardware["PWR"]:
                self.pwr.config("V_ONCE,I_ONCE")
            if self.hardware["GPS"]:
                self.en_gps.value = False
            self.power_mode = "minimum"

        elif "norm" in mode:
            self.enable_rf.value = True
            if self.hardware["IMU"]:
                self.reinit("IMU")
            if self.hardware["PWR"]:
                self.pwr.config("V_CONT,I_CONT")
            if self.hardware["GPS"]:
                self.en_gps.value = True
            self.power_mode = "normal"
            # don't forget to reconfigure radios, gps, etc...

    def burn(self, burn_num, dutycycle=0, freq=1000, duration=1):
        """
        Operate burn wire circuits. Wont do anything unless the a nichrome burn wire
        has been installed.

        IMPORTANT: See "Burn Wire Info & Usage" of https://pycubed.org/resources
        before attempting to use this function!

        burn_num:  (string) which burn wire circuit to operate, must be either '1' or '2'
        dutycycle: (float) duty cycle percent, must be 0.0 to 100
        freq:      (float) frequency in Hz of the PWM pulse, default is 1000 Hz
        duration:  (float) duration in seconds the burn wire should be on
        """
        # convert duty cycle % into 16-bit fractional up time
        dtycycl = int((dutycycle / 100) * (0xFFFF))
        print("----- BURN WIRE CONFIGURATION -----")
        print(
            "\tFrequency of: {}Hz\n\tDuty cycle of: {}% (int:{})\n\tDuration of {}sec".format(
                freq, (100 * dtycycl / 0xFFFF), dtycycl, duration
            )
        )
        # create our PWM object for the respective pin
        # not active since duty_cycle is set to 0 (for now)
        if "1" in burn_num:
            burnwire = pwmio.PWMOut(board.BURN1, frequency=freq, duty_cycle=0)
        elif "2" in burn_num:
            burnwire = pwmio.PWMOut(board.BURN2, frequency=freq, duty_cycle=0)
        else:
            return False
        # Configure the relay control pin & open relay
        self._relayA.drive_mode = digitalio.DriveMode.PUSH_PULL
        self._relayA.value = 1
        self.RGB = (255, 0, 0)
        # Pause to ensure relay is open
        time.sleep(0.5)
        # Set the duty cycle over 0%
        # This starts the burn!
        burnwire.duty_cycle = dtycycl
        time.sleep(duration)
        # Clean up
        self._relayA.value = 0
        burnwire.duty_cycle = 0
        self.RGB = (0, 0, 0)
        burnwire.deinit()
        self._relayA.drive_mode = digitalio.DriveMode.OPEN_DRAIN
        return True

    def boot_sequence(self) -> list[int]:
        pass

    def run_system_diagnostics(self) -> list[int]:
        pass
