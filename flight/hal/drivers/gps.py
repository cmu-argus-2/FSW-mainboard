"""
Author: Chase
Description: GPS Driver for the SkyTraq PX1120S and S1216F8-GL Modules

This driver is designed to interface with the SkyTraq PX1120S and S1216F8-GL GPS modules over
UART using their binary protocol. It handles board detection, message parsing, and data extraction for navigation information.

Note, the PX1120S uses the AN0037 binary protocol, while the S1216F8-GL uses the AN0030 binary protocol.
The driver automatically detects the board type based on the incoming messages and parses the data accordingly.

For final flight build, anything related to the PX1120S SHOULD be removed, as the S1216F8-GL is the receiver that will be used.
"""

try:
    import struct
    from typing import Optional

    from busio import UART
    from digitalio import DigitalInOut
except ImportError:
    pass


EPOCH_YEAR = 1980
EPOCH_MONTH = 1
EPOCH_DAY = 6


class GPS:
    def __init__(
        self, uart: UART, enable=None, debug: bool = False, mock: bool = False
    ) -> None:  # TODO GPS Enable is obsolete
        self._uart = uart
        self.debug = debug

        # Board Detection
        self._board = None
        self._board_detected = False
        self._ordered_keys_map = {
            "PX1120S": [
                "message_id",
                "fix_mode",
                "number_of_sv",
                "week",
                "tow",
                "latitude",
                "longitude",
                "ellipsoid_altitude",
                "mean_sea_level_altitude",
                "gdop",
                "pdop",
                "hdop",
                "vdop",
                "tdop",
                "ecef_x",
                "ecef_y",
                "ecef_z",
                "ecef_vx",
                "ecef_vy",
                "ecef_vz",
                "unix_time",
                "timestamp_utc",
            ],
            "S1216F8-GL": [
                "message_id",
                "IOD",
                "fix_mode",
                "week",
                "tow",
                "ecef_x",
                "ecef_y",
                "ecef_z",
                "ecef_vx",
                "ecef_vy",
                "ecef_vz",
                "clock_bias",
                "clock_drift",
                "GDOP",
                "PDOP",
                "HDOP",
                "VDOP",
                "TDOP",
                "unix_time",
                "timestamp_utc",
            ],
        }

        # Payload Buffer:
        self._payload = bytearray([0] * 59)

        # Message Variables
        self._msg = None
        self._payload_len = 0
        self._msg_id = 0
        self._msg_cs = 0

        # Helper Flags for Receiver Hardware Configuration
        # Setting to True will run the configuration function once
        self._reset_to_factory = False
        self._binary_set_flag = False  # This must be true for the S1216F8-GL
        self._periodic_nav_flag = False  # This must be true for the S1216F8-GL
        self._disable_nmea_flag = False
        self._queried_binary_status_flag = False
        self._disable_unnecessary_binary_flag = False

        if self.debug:
            self._nav_data_hex = {}  # Navigation data as a dictionary of hex values

        # GPS Data Fields
        # TODO: THIS DOES NOT CURRENTLY WORK WITH SPLAT, INT TO FLOAT CONVERSION ERROR

        # Initialize null starting values for all GPS data
        # These values are used for logging and will be ints
        self.timestamp_utc = None  # UTC as a dictionary in the form {year, month, day, hour, minute, second}

        self.unix_time = 0  # Unix time in seconds, type: float = float (f), unit: seconds

        ## For AN0030: Binary Protocol
        self.message_id = 0  # Field 1, type: uint8, unit: N/A
        self.IOD = 0  # Field 2, type: uint8, unit: N/A
        self.fix_mode = 0  # Field 3, type: uint8, unit: N/A
        self.week = 0  # Field 4-5, type: uint16, unit: N/A
        self.tow = 0  # Field 6-13, type: double-precision float, unit: seconds
        self.ecef_x = 0  # Field 14-21, type: double-precision float, unit: meters
        self.ecef_y = 0  # Field 22-29, type: double-precision float, unit: meters
        self.ecef_z = 0  # Field 30-37, type: double-precision float, unit: meters
        self.ecef_vx = 0  # Field 38-41, type: single-precision float, unit: meters per second
        self.ecef_vy = 0  # Field 42-45, type: single-precision float, unit: meters per second
        self.ecef_vz = 0  # Field 46-49, type: single-precision float, unit: meters per second
        self.clock_bias = 0  # Field 50-57, type: double-precision float, unit: seconds
        self.clock_drift = 0  # Field 58-61, type: single-precision float, unit: seconds per second
        self.gdop = 0  # Field 62-65, type: single-precision float, unit: N/A
        self.pdop = 0  # Field 66-69, type: single-precision float, unit: N/A
        self.hdop = 0  # Field 70-73, type: single-precision float, unit: N/A
        self.vdop = 0  # Field 74-77, type: single-precision float, unit: N/A
        self.tdop = 0  # Field 78-81, type: single-precision float, unit: N/A

        ## For AN0037: Binary Protocol
        self.number_of_sv = 0  # Field 3, type: uint8 = unsigned byte (B), unit: N/A
        self.latitude = 0  # Field 10-13, type: sint32 = signed long (l), unit: 1/1e-7 degrees
        self.longitude = 0  # Field 14-17, type: sint32 = signed long (l), unit: 1/1e-7 degrees
        self.ellipsoid_altitude = 0  # Field 18-21, type: sint32 = signed long (l), unit: 1/100 meters
        self.mean_sea_level_altitude = 0  # Field 22-25, type: sint32 = signed long (l), unit: 1/100 meters

        # TODO : This needs to be removed for any infield testing
        self.mock = mock
        if self.mock:
            # From app note:
            # self.mock_message = (
            # b"\xa0\xa1\x00\x3b\xa8\x02\x07\x08\x6a\x03\x21\x7a\x1f\x1b\x1f\x16\xf1\xb6\xe1"
            # b"\x3c\x1c\x00\x00\x0f\x6f\x00\x00\x17\xb7\x01\x0d\x00\xe4\x00\x7e\x00\xbd\x00"
            # b"\x8f\xf1\x97\x18\xd2\xe9\x88\x7d\x90\x1a\xfb\x26\xf7\x03\xF5\x09\xFE\x01\x79"
            # b"\x7C\x4A\xFB\x9B\xA8\x40\x68\x0d\x0a"
            # )
            # From Ridge Test:
            self.mock_message = (
                b"\xa0\xa1\x00\x3b\xa8\x02\x0f\x09\x26\x01\x66\x7a\x4f\x18\x1e\xac\x4f\xd0\x71"
                b"\x40\xae\x00\x00\x91\x87\x00\x00\x9e\x7f\x00\xb1\x00\x96\x00\x56\x00\x7b\x00"
                b"\x5d\x05\x22\x92\x4e\xe3\x7e\x60\xe7\x18\x8b\x33\x6f\xff\xff\xff\xff\xff\xff"
                b"\xff\xfe\x00\x00\x00\x00\xfd\x0d\x0a"
            )

        super().__init__()

    def update(self) -> bool:

        ## COLLECT THE MESSAGE
        if self.mock:
            self._msg = self.mock_message
        else:
            try:
                self._msg = self._read_sentence()
            except UnicodeError:
                print("Unicode Error when parsing GPS message")
                return False

        if self._msg is None:
            if self.debug:
                print("GPS message is None")
            return False
        if len(self._msg) < 7:
            if self.debug:
                print(f"GPS message too short: {len(self._msg)} bytes")
            return False

        # Print the raw messages
        if self.debug:
            if self.mock:
                print("Mock message: \n", " ".join(f"{b:02X}" for b in self._msg))
            else:
                print("RAW")
                print(self._msg)
                print("DECODE")
                print(" ".join(f"{b:02x}" for b in self._msg))

        ## CHECK BOARD TYPE
        if (self._msg_id == 0xA8 or self._msg == b"$SkyTraq,Phoenix\r\n") and not self._board_detected:
            if self.debug:
                print("Board type detected: PX1120S")
            self._board = "PX1120S"
            self._board_detected = True

        if (
            self._msg_id == 0xDF or self._msg == b"$PSTI,001,1*1E\r\n" or self._msg == b"$SkyTraq,Venus8\r\n"
        ) and not self._board_detected:
            if self.debug:
                print("Board type detected: S1216F8-GL")
            self._board = "S1216F8-GL"
            self._board_detected = True

            # For the S1216F8-GL, this needs to run every time the receiver is powered on, there is no way to flash it
            self.enable_periodic_nav_data()
            self.set_to_binary()

            if self.debug:
                # print("SET TO BINARY")
                print("ENABLING PERIODIC NAV DATA ENABLING PERIODIC NAV DATA ")

        if self._board is None:
            if self.debug:
                print("Board type could not be detected.")
            return False

        ## CONFIGURE THE RECEIVER (Once-per-cycle flags)
        self.use_helper_functions

        ## VALIDATE MESSAGE
        if self._msg[0] != 0xA0 or self._msg[1] != 0xA1:
            if self.debug:
                print("Invalid start bytes, expected 0xA0 0xA1, got: ", hex(self._msg[0]), hex(self._msg[1]))
            return False

        ## PARSE MESSAGE
        # Parse message length, ID, checksum, and payload
        try:
            self._payload_len = int(((self._msg[2] & 0xFF) << 8) | self._msg[3])
            self._msg_id = int(self._msg[4])
            self._msg_cs = int(self._msg[-3])
            self._payload = bytearray(self._msg[4:-3])  # TODO Is this required
        except Exception as e:
            if self.debug:
                print("Error parsing message length, ID, checksum, or payload:", e)
            return False

        ## CHECK PAYLOAD MESSAGE AND ACK
        if self.debug:
            print("Payload:\n", " ".join(f"{b:02X}" for b in self._payload))
        if self._msg_id == 0x83:  # 0x83 is successful ACK of setting binary nav type
            return False

        ## CHECK NAV DATA
        if self._msg_id != 0xA8 and self._msg_id != 0xDF:
            if self.debug:
                print("Invalid message ID, expected 0xA8 or 0xdf, got: ", hex(self._msg_id))
            return False

        ## CHECKSUM
        if not self.checksum():
            if self.debug:
                print("Checksum failed!")
            return False

        ## PARSE NAV DATA
        if self._board == "PX1120S":
            if self._payload_len != 59:
                if self.debug:
                    print("Invalid payload length, expected 59, got: ", self._payload_len)
                return False
            return self.parse_data_AN0037()

        if self._board == "S1216F8-GL":
            if self._payload_len != 81:
                if self.debug:
                    print("Invalid payload length, expected 81, got: ", self._payload_len)
                return False
            return self.parse_data_AN0030()

        return False

    def checksum(self) -> int:  # Checksum is simply XOR sequentially of the payload ID + payload bytes
        cs = 0
        for i in self._payload:
            i = int(i)
            cs ^= i
        if cs != self._msg_cs:
            if self.debug:
                print("Checksum failed!")
            return False
        return cs

    def parse_data_AN0037(self) -> bool:
        """
        Parse SkyTraq AN0037 Navigation Data Message (ID 0xA8) payload using the
        same style as parse_data_AN0030 (typed helpers, no manual bit shifting). :contentReference[oaicite:0]{index=0}
        """
        try:
            self.message_id = self._u8(0)
            self.fix_mode = self._u8(1)
            self.number_of_sv = self._u8(2)
            self.week = self._u16(3)
            # per AN0037, many parameters are scaled by 100, this is different than AN0030
            self.tow = self._u32(5) / 100.0
            self.latitude = self._s32(self._u32(9)) / 100.0
            self.longitude = self._s32(self._u32(13)) / 100.0
            self.ellipsoid_altitude = self._s32(self._u32(17)) / 100.0
            self.mean_sea_level_altitude = self._s32(self._u32(21)) / 100.0
            self.gdop = self._u16(25) / 100.0
            self.pdop = self._u16(27) / 100.0
            self.hdop = self._u16(29) / 100.0
            self.vdop = self._u16(31) / 100.0
            self.tdop = self._u16(33) / 100.0
            self.ecef_x = self._s32(self._u32(35)) / 100.0
            self.ecef_y = self._s32(self._u32(39)) / 100.0
            self.ecef_z = self._s32(self._u32(43)) / 100.0
            self.ecef_vx = self._s32(self._u32(47)) / 100.0
            self.ecef_vy = self._s32(self._u32(51)) / 100.0
            self.ecef_vz = self._s32(self._u32(55)) / 100.0
            self.unix_time = self.gps_time_2_unix_time(self.week, self.tow)

            if self.debug:
                print("PRINTING NAV DATA PRINTING NAV DATA PRINTING NAV DATA ")
                self.print_nav_data()
            return True

        except Exception as e:
            print(f"Error parsing data: {e}")
            return False

    def parse_data_AN0030(self) -> bool:
        try:
            self.message_id = self._u8(0)
            self.IOD = self._u8(1)
            self.fix_mode = self._u8(2)
            self.week = self._u16(3)
            self.tow = self._dpfp(5)
            self.ecef_x = self._dpfp(13)
            self.ecef_y = self._dpfp(21)
            self.ecef_z = self._dpfp(29)
            self.ecef_vx = self._spfp(37)
            self.ecef_vy = self._spfp(41)
            self.ecef_vz = self._spfp(45)
            self.clock_bias = self._dpfp(49)
            self.clock_drift = self._spfp(57)
            self.gdop = self._spfp(61)
            self.pdop = self._spfp(65)
            self.hdop = self._spfp(69)
            self.vdop = self._spfp(73)
            self.tdop = self._spfp(77)
            self.unix_time = self.gps_time_2_unix_time(self.week, self.tow)
            if self.debug:
                print("PRINTING NAV DATA PRINTING NAV DATA PRINTING NAV DATA ")
                self.print_nav_data()
            return True
        except Exception as e:
            print(f"Error parsing data: {e}")
            return False

    def _s32(self, value: int) -> int:
        return value if value < 0x80000000 else value - 0x100000000

    def _u8(self, idx: int) -> int:
        return self._payload[idx] & 0xFF

    def _u16(self, idx: int) -> int:
        return (self._payload[idx] << 8) | self._payload[idx + 1]

    def _u32(self, idx: int) -> int:
        return (
            (self._payload[idx] << 24)
            | (self._payload[idx + 1] << 16)
            | (self._payload[idx + 2] << 8)
            | self._payload[idx + 3]
        )

    def _u64(self, idx: int) -> int:
        return (
            (self._payload[idx] << 56)
            | (self._payload[idx + 1] << 48)
            | (self._payload[idx + 2] << 40)
            | (self._payload[idx + 3] << 32)
            | (self._payload[idx + 4] << 24)
            | (self._payload[idx + 5] << 16)
            | (self._payload[idx + 6] << 8)
            | self._payload[idx + 7]
        )

    def _spfp(self, idx: int) -> float:
        return struct.unpack(">f", bytes(self._payload[idx : idx + 4]))[0]

    def _dpfp(self, idx: int) -> float:
        return struct.unpack(">d", bytes(self._payload[idx : idx + 8]))[0]

    """
    Fix Modes in GPS Binary Message:

    0 - No fix: The GPS receiver has not obtained a valid fix or has lost the fix.
    1 - GPS fix: A 2D fix is available (latitude and longitude, but altitude is not necessarily reliable).
    3 - 3D fix: A 3D fix is available (latitude, longitude, and altitude are all valid and reliable).
    4 - 3D + GNSS fix: A fix using signals from multiple GNSS systems (e.g., GPS, GLONASS, Galileo, BeiDou).
    """

    def has_fix(self) -> bool:
        """True if a current fix for location information is available."""
        if self.fix_mode is not None and self.fix_mode >= 1:
            return True
        else:
            return False

    def has_3d_fix(self) -> bool:
        """Returns true if there is a 3d fix available.
        use has_fix to determine if a 2d fix is available,
        passing it the same data"""
        if self.fix_mode is not None and self.fix_mode >= 2:
            return True
        else:
            return False

    # TODO: Check if the datetime library can be used rather than manually counting
    def gps_time_2_unix_time(self, gps_week: int, tow: float) -> float:
        # Number of days in each month (non-leap year)
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

        # Helper function to check for leap years
        def is_leap_year(year):
            return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

        # Split TOW into whole-day and sub-day components
        tow_day_offset = int(tow // 86400)
        seconds_in_day = tow - (tow_day_offset * 86400)

        # Calculate the total number of days from GPS week and TOW day rollover
        total_days = gps_week * 7 + tow_day_offset

        # Start from the epoch date and add total days
        year = EPOCH_YEAR
        month = EPOCH_MONTH
        day = EPOCH_DAY

        while total_days > 0:
            # Adjust days in February for leap years
            if is_leap_year(year):
                days_in_month[1] = 29
            else:
                days_in_month[1] = 28

            # Check if remaining days fit in the current month
            if total_days >= (days_in_month[month - 1] - day + 1):
                total_days -= days_in_month[month - 1] - day + 1
                day = 1
                month += 1
                if month > 12:
                    month = 1
                    year += 1
            else:
                day += total_days
                total_days = 0

        # Convert days to seconds for Unix time calculation
        days_since_unix_epoch = (year - 1970) * 365 + sum(is_leap_year(y) for y in range(1970, year))
        for m in range(1, month):
            days_since_unix_epoch += days_in_month[m - 1]
        days_since_unix_epoch += day - 1

        # Convert days to seconds and add sub-day TOW seconds
        unix_time = days_since_unix_epoch * 86400 + seconds_in_day

        # Calculate hours, minutes, and seconds
        hours = int(seconds_in_day // 3600)
        minutes = int((seconds_in_day % 3600) // 60)
        seconds = seconds_in_day % 60

        self.timestamp_utc = {
            "year": year,
            "month": month,
            "day": day,
            "hour": hours,
            "minute": minutes,
            "second": round(seconds, 2),
        }

        # Return the unix time
        return unix_time

    def print_nav_data(self) -> None:
        """Prints the current navigation data to the console."""
        if self._board is not None:
            self.nav_data = self.get_nav_data()
            ordered_keys = self._ordered_keys_map.get(self._board, list(self.nav_data.keys()))

            for key in ordered_keys:
                if key in self.nav_data:
                    print(f"{key}: {self.nav_data[key]}")

    def get_nav_data(self) -> dict:
        """Returns the current navigation data as a dictionary."""
        if self._board is None:
            return {}
        elif self._board == "PX1120S":
            return {
                "message_id": self.message_id,
                "fix_mode": self.fix_mode,
                "number_of_sv": self.number_of_sv,
                "week": self.week,
                "tow": self.tow,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "ellipsoid_altitude": self.ellipsoid_altitude,
                "mean_sea_level_altitude": self.mean_sea_level_altitude,
                "gdop": self.gdop,
                "pdop": self.pdop,
                "hdop": self.hdop,
                "vdop": self.vdop,
                "tdop": self.tdop,
                "ecef_x": self.ecef_x,
                "ecef_y": self.ecef_y,
                "ecef_z": self.ecef_z,
                "ecef_vx": self.ecef_vx,
                "ecef_vy": self.ecef_vy,
                "ecef_vz": self.ecef_vz,
                "unix_time": self.unix_time,
                "timestamp_utc": self.timestamp_utc,
            }
        elif self._board == "S1216F8-GL":
            return {
                "message_id": self.message_id,
                "IOD": self.IOD,
                "fix_mode": self.fix_mode,
                "week": self.week,
                "tow": self.tow,
                "ecef_x": self.ecef_x,
                "ecef_y": self.ecef_y,
                "ecef_z": self.ecef_z,
                "ecef_vx": self.ecef_vx,
                "ecef_vy": self.ecef_vy,
                "ecef_vz": self.ecef_vz,
                "clock_bias": self.clock_bias,
                "clock_drift": self.clock_drift,
                "gdop": self.gdop,
                "pdop": self.pdop,
                "hdop": self.hdop,
                "vdop": self.vdop,
                "tdop": self.tdop,
                "unix_time": self.unix_time,
                "timestamp_utc": self.timestamp_utc,
            }
        return self._nav_data_hex

    def write(self, bytestr) -> Optional[int]:
        return self._uart.write(bytestr)

    def send_binary(self, bytestr) -> None:
        self.write(bytestr)

    def set_to_binary(self) -> None:
        """Send Set to Binary Mode command (Message ID 0x09)."""
        self.write(b"\xa0\xa1\x00\x03\x09\x02\x00\x0b\x0d\x0a")
        # self.write(b"\xa0\xa1\x00\x03\x09\x02\x01\x0a\x0d\x0a") # Flash memory version

    def query_binary_status(self) -> None:
        """Send Query Binary Status command."""
        if self._board == "PX1120S":
            # (Message ID 0x16)
            self.write(b"\xa0\xa1\x00\x01\x16\x16\x0d\x0a")
        if self._board == "S1216F8-GL":
            # (Message ID 0x1F)
            self.write(b"\xa0\xa1\x00\x01\x1F\x1F\x0d\x0a")

    def enable_periodic_nav_data(self) -> None:
        """Send Enable Periodic Navigation Data command."""
        if self._board == "PX1120S":
            # (Message ID 0x64)
            # self.write(b"\xa0\xa1\x00\x04\x64\x2F\x01\x00\x4A\x0d\x0a")
            self.write(b"\xa0\xa1\x00\x04\x64\x2F\x01\x01\x4B\x0d\x0a")  # Flash memory version
        if self._board == "S1216F8-GL":
            # (Message ID 0x11)
            self.write(b"\xa0\xa1\x00\x09\x1e\x00\x00\x00\x00\x01\x03\x00\x00\x1c\x0d\x0a")
            # self.write(b"\xa0\xa1\x00\x09\x1e\x00\x00\x00\x00\x01\x03\x00\x01\x1d\x0d\x0a") # Flash memory version, this does not work

    def disable_nmea_periodic(self) -> None:
        """Send Disable NMEA Periodic Messages command (Message ID 0x64)."""
        self.write(b"\xa0\xa1\x00\x0F\x64\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x67\x0d\x0a")

    def query_nav_data(self) -> None:
        """Send Query Navigation Data command (Message ID 0x10)."""
        self.write(b"\xa0\xa1\x00\x01\x10\x10\x0d\x0a")  # This queries the wrong thing!

    def reset_to_factory_defaults(self) -> None:
        """Send Reset to Factory Defaults command (Message ID 0x04)."""
        self.write(b"\xa0\xa1\x00\x02\x04\x00\x04\x0d\x0a")

    def disable_unnecessary_binary_data(self) -> None:
        """Send Disable Unecessary Nav Binary Messages command (Message ID 0x1E)."""
        self.write(b"\xa0\xa1\x00\x09\x1e\x00\x00\x00\x00\x01\x03\x00\x00\x1c\x0d\x0a")

    def use_helper_functions(self) -> None:
        """Use helper functions to set up the receiver hardware configuration."""
        if self._board == "PX1120S":
            if self.debug:
                print("Helper Functions: PX1120S")

            # Helper Statements
            if self._reset_to_factory:
                self.reset_to_factory_defaults()
                self._reset_to_factory = False
                if self.debug:
                    print("RESETTING TO FACTORY DEFAULTS RESETTING TO FACTORY DEFAULTS ")

            if self._disable_nmea_flag:
                self.disable_nmea_periodic()
                self._disable_nmea_flag = False
                if self.debug:
                    print("DISABLING NMEA DISABLING NMEA DISABLING NMEA ")

            if self._binary_set_flag:
                self.set_to_binary()
                self._binary_set_flag = False
                if self.debug:
                    print("SETTING TO BINARY SETTING TO BINARY SETTING TO BINARY ")

            if self._queried_binary_status_flag:
                self.query_binary_status()
                self._queried_binary_status_flag = False
                if self.debug:
                    print("QUERYING BINARY STATUS QUERYING BINARY STATUS ")

            if self._periodic_nav_flag:
                self.enable_periodic_nav_data()
                self._periodic_nav_flag = False
                if self.debug:
                    print("ENABLING PERIODIC NAV DATA ENABLING PERIODIC NAV DATA ")

        if self._board == "S1216F8-GL":
            if self.debug:
                print("Helper Functions: S1216F8-GL")
                # Note, the S1216F8-GL and PX1120S don't have all the same helper functions
                # This is due to the different protocols

            # Helper Statements
            if self._reset_to_factory:
                self.reset_to_factory_defaults()
                self._reset_to_factory = False
                if self.debug:
                    print("RESETTING TO FACTORY DEFAULTS RESETTING TO FACTORY DEFAULTS ")

            if self._binary_set_flag:
                self.set_to_binary()
                self._binary_set_flag = False
                if self.debug:
                    print("SETTING TO BINARY SETTING TO BINARY SETTING TO BINARY ")

            if self._queried_binary_status_flag:
                self.query_binary_status()
                self._queried_binary_status_flag = False
                if self.debug:
                    print("QUERYING BINARY STATUS QUERYING BINARY STATUS ")

            if self._periodic_nav_flag:
                self.enable_periodic_nav_data()
                self._periodic_nav_flag = False
                if self.debug:
                    print("ENABLING PERIODIC NAV DATA ENABLING PERIODIC NAV DATA ")

            if self._disable_unnecessary_binary_flag:
                self.disable_unnecessary_binary_data()
                self._disable_unnecessary_binary_flag = False
                if self.debug:
                    print("DISABLING UNNECESSARY BINARY DATA DISABLING UNNECESSARY BINARY DATA ")

    @property
    def in_waiting(self) -> int:
        return self._uart.in_waiting

    def readline(self) -> Optional[bytes]:
        return self._uart.readline()

    def read(self, nbytes: int) -> Optional[bytes]:
        return self._uart.read(nbytes)

    def _read_sentence(self) -> Optional[bytes]:
        # Need at least 65 bytes for nav data message: 2 start + 2 len + 59 payload + 1 cs + 2 end = 66

        if self.in_waiting < 8:
            return None
        return self._uart.readline()

    def enable(self) -> None:
        """Enable the GPS module through the enable pin"""
        self.__enable = True

    def disable(self) -> None:
        """Disable the GPS module through the enable pin"""
        self.__enable = False

    ######################## ERROR HANDLING ########################

    @property
    def device_errors(self):
        return []

    def deinit(self):
        if self._enable is not None:
            self._enable.deinit()
            self._enable = None
        return
