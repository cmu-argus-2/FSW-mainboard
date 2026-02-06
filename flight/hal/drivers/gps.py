
try:
    import struct

    from typing import Optional

    from busio import UART
    from digitalio import DigitalInOut
except ImportError:
    pass


EPOCH_YEAR = 1980
EPOCH_MONTH = 1
EPOCH_DAY = 5


class GPS:
    def __init__(self, uart: UART, enable = None, debug: bool = False, mock: bool = True) -> None: # TODO GPS Enable is obsolete
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
                "navigation_state",
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
        self._reset_to_factory = False
        self._binary_set_flag = False
        self._periodic_nav_flag = False
        self._disable_nmea_flag = False
        self._queried_binary_status_flag = False
        self._disable_unnecessary_binary_flag = False

        if self.debug:
            self._nav_data_hex = {}  # Navigation data as a dictionary of hex values
   
            # self.data_strings = {  # Navigation data as a dictionary of strings for debugging
            #     "message_id": "None",
            #     "fix_mode": "None",
            #     "number_of_sv": "None",
            #     "gps_week": "None",
            #     "tow": "None",
            #     "latitude": "None",
            #     "longitude": "None",
            #     "ellipsoid_alt": "None",
            #     "mean_sea_lvl_alt": "None",
            #     "gdop": "None",
            #     "pdop": "None",
            #     "hdop": "None",
            #     "vdop": "None",
            #     "tdop": "None",
            #     "ecef_x": "None",
            #     "ecef_y": "None",
            #     "ecef_z": "None",
            #     "ecef_vx": "None",
            #     "ecef_vy": "None",
            #     "ecef_vz": "None",
            # }

        # GPS Data Fields
        # TODO: Check the formats of these values as used in the FSW
        # Initialize null starting values for all GPS data
        # These values are used for logging and will be ints
        self.timestamp_utc = None  # UTC as a dictionary in the form {year, month, day, hour, minute, second}

        self.unix_time = None  # Unix time in seconds, type: float = float (f), unit: seconds

        ## For AN0030: Binary Protocol
        self.message_id = None # Field 1, type: uint8, unit: N/A
        self.IOD = None # Field 2, type: uint8, unit: N/A
        self.navigation_state = None # Field 3, type: uint8, unit: N/A
        self.week = None # Field 4-5, type: uint16, unit: N/A
        self.tow = None # Field 6-13, type: double-precision float, unit: seconds
        self.ecef_x = None # Field 14-21, type: double-precision float, unit: meters
        self.ecef_y = None # Field 22-29, type: double-precision float, unit: meters
        self.ecef_z = None # Field 30-37, type: double-precision float, unit: meters
        self.ecef_vx = None # Field 38-41, type: single-precision float, unit: meters per second
        self.ecef_vy = None # Field 42-45, type: single-precision float, unit: meters per second
        self.ecef_vz = None # Field 46-49, type: single-precision float, unit: meters per second
        self.clock_bias = None # Field 50-57, type: double-precision float, unit: seconds
        self.clock_drift = None # Field 58-61, type: single-precision float, unit: seconds per second
        self.GDOP = None # Field 62-65, type: single-precision float, unit: N/A
        self.PDOP = None # Field 66-69, type: single-precision float, unit: N/A
        self.HDOP = None # Field 70-73, type: single-precision float, unit: N/A
        self.VDOP = None # Field 74-77, type: single-precision float, unit: N/A
        self.TDOP = None # Field 78-81, type: single-precision float, unit: N/A

        ## For AN0037: Binary Protocol
        self.message_id = None  # Field 1, type: uint8 = unsigned byte (B), unit: N/A
        self.fix_mode = None  # Field 2, type: uint8 = unsigned byte (B), unit: N/A
        self.number_of_sv = None  # Field 3, type: uint8 = unsigned byte (B), unit: N/A
        self.week = None  # Field 4-5, type: uint16 = unsigned short (H), unit: N/A
        self.tow = None  # Field 6-9, type: uint32 = unsigned long (L), unit: N/A
        self.latitude = None  # Field 10-13, type: sint32 = signed long (l), unit: 1/1e-7 degrees
        self.longitude = None  # Field 14-17, type: sint32 = signed long (l), unit: 1/1e-7 degrees
        self.ellipsoid_altitude = None  # Field 18-21, type: sint32 = signed long (l), unit: 1/100 meters
        self.mean_sea_level_altitude = None  # Field 22-25, type: sint32 = signed long (l), unit: 1/100 meters
        self.gdop = None  # Field 26-27, type: uint16 = unsigned short (H), unit: 1/100
        self.pdop = None  # Field 28-29, type: uint16 = unsigned short (H), unit: 1/100
        self.hdop = None  # Field 30-31, type: uint16 = unsigned short (H), unit: 1/100
        self.vdop = None  # Field 32-33, type: uint16 = unsigned short (H), unit: 1/100
        self.tdop = None  # Field 34-35, type: uint16 = unsigned short (H), unit: 1/100
        self.ecef_x = None  # Field 36-39, type: sint32 = signed long (l), unit: 1/100 meters
        self.ecef_y = None  # Field 40-43, type: sint32 = signed long (l), unit: 1/100 meters
        self.ecef_z = None  # Field 44-47, type: sint32 = signed long (l), unit: 1/100 meters
        self.ecef_vx = None  # Field 48-51, type: sint32 = signed long (l), unit: 1/100 meters per second
        self.ecef_vy = None  # Field 52-55, type: sint32 = signed long (l), unit: 1/100 meters per second
        self.ecef_vz = None  # Field 56-59, type: sint32 = signed long (l), unit: 1/100 meters per second

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

        # else:
        #     # Module expected to actually exist, send nav_data request to module
        #     # print("GPS Module Initi alized, setting to binary mode")
        #     # self.set_to_binary()

        super().__init__()

    def update(self) -> bool:
        # if self._reset_to_factory is False:
        #     self.reset_to_factory_defaults()
        #     self._reset_to_factory = True
        #     print('RESETTING TO FACTORY DEFAULTS RESETTING TO FACTORY DEFAULTS ')

        # if not self._disable_nmea_flag:
        #     self.disable_nmea_periodic()
        #     self._disable_nmea_flag = True
        #     print('DISABLING NMEA DISABLING NMEA DISABLING NMEA ')

        # if not self._binary_set_flag and not self.mock:
        #     self.set_to_binary()
        #     self._binary_set_flag = True
        #     print('SETTING TO BINARY SETTING TO BINARY SETTING TO BINARY ')

        # if not self._queried_binary_status_flag:
        #     self.query_binary_status()
        #     self._queried_binary_status_flag = True
        #     print('QUERYING BINARY STATUS QUERYING BINARY STATUS ')

        # if not self._periodic_nav_flag:
        #     self.enable_periodic_nav_data()
        #     # self._periodic_nav_flag = True
        #     print('ENABLING PERIODIC NAV DATA ENABLING PERIODIC NAV DATA ')

        if not self._disable_unnecessary_binary_flag:
            self.disable_unnecessary_binary_data()
            self._disable_unnecessary_binary_flag = True
            print('DISABLING UNNECESSARY BINARY DATA DISABLING UNNECESSARY BINARY DATA ')

        if self.mock:
            self._msg = self.mock_message
        else:
            try:
                self._msg = self._read_sentence()
            except UnicodeError:
                print("Unicode Error when parsing GPS message")
                return False
            if self._msg is None:
                print("GPS message is None")
                return False
            if len(self._msg) < 7:
                print(f"GPS message too short: {len(self._msg)} bytes")
                print(self._msg)
                return False

        if self.debug:
            if self.mock:
                print("Mock message: \n", ' '.join(f'{b:02X}' for b in self._msg))
            else:
                print("RAW")
                print(self._msg)
                print("DECODE")
                print(" ".join(f"{b:02x}" for b in self._msg))

        ## Validate the message is correct
        if self._msg[0] != 0xA0 or self._msg[1] != 0xA1:
            if self.debug:
                print("Invalid start bytes, expected 0xA0 0xA1, got: ", hex(self._msg[0]), hex(self._msg[1]))
            return False
        
        # Parse message length, ID, checksum, and payload
        try:
            self._payload_len = int(((self._msg[2] & 0xFF) << 8) | self._msg[3])
            self._msg_id = int(self._msg[4])
            self._msg_cs = int(self._msg[-3])
            self._payload = bytearray(self._msg[4:-3]) # TODO Is this required
        except Exception as e:
            if self.debug:
                print("Error parsing message length, ID, checksum, or payload:", e)
            return False

        if self.debug:
            print("Payload:\n", ' '.join(f'{b:02X}' for b in self._payload))
        if self._msg_id == 0x83: # 0x83 is successful ACK of setting binary nav type
            return False

        ## Check which board/protocol this is
        if self._msg_id != 0xA8 and self._msg_id != 0xdf:
            if self.debug:
                print("Invalid message ID, expected 0xA8 or 0xdf, got: ", hex(self._msg_id))
            return False

        if self._msg_id == 0xA8 and not self._board_detected:
            self._board = "PX1120S"
            self._board_detected = True

        if self._msg_id == 0xdf and not self._board_detected:
            self._board = "S1216F8-GL"
            self._board_detected = True

        if self._board is None:
            if self.debug:
                print("Board type could not be detected.")
            return False

        if not self.checksum():
            if self.debug:
                print("Checksum failed!")
            return False

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

    def checksum(self) -> int: # Checksum is simply XOR sequentially of the payload ID + payload bytes
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
        # if not self._nav_data_hex:
        #     return
        # self.message_id = self._nav_data_hex["message_id"]
        # self.fix_mode = self.parse_fix_mode()
        # self.number_of_sv = int(self._nav_data_hex["number_of_sv"])
        # self.week = int(self._nav_data_hex["gps_week"])
        # self.tow = int(self._nav_data_hex["tow"])
        # self.latitude = self.parse_lat()
        # self.longitude = self.parse_lon()
        # self.ellipsoid_altitude = self.parse_elip_alt()
        # self.mean_sea_level_altitude = self.parse_msl_alt()
        # self.gdop = self.parse_gdop()
        # self.pdop = self.parse_pdop()
        # self.hdop = self.parse_hdop()
        # self.vdop = self.parse_vdop()
        # self.tdop = self.parse_tdop()
        # self.ecef_x = self.parse_ecef_x()
        # self.ecef_y = self.parse_ecef_y()
        # self.ecef_z = self.parse_ecef_z()
        # self.ecef_vx = self.parse_ecef_vx()
        # self.ecef_vy = self.parse_ecef_vy()
        # self.ecef_vz = self.parse_ecef_vz()
        # self.timestamp_utc = self.gps_datetime(self.week, self.tow)
        try:
            self.message_id = self._u8(0)
            self.fix_mode = self._u8(1)
            self.number_of_sv = self._u8(2)
            self.week = self._u16(3)
            self.tow = self._u32(5)/100
            self.latitude = self._signed_32bit(
                (self._payload[9] << 24) | (self._payload[10] << 16) | (self._payload[11] << 8) | self._payload[12]
            )/100
            self.longitude = self._signed_32bit(
                ((self._payload[13] << 24) | (self._payload[14] << 16) | (self._payload[15] << 8) | self._payload[16])
            )/100
            self.ellipsoid_altitude = self._signed_32bit(
                ((self._payload[17] << 24) | (self._payload[18] << 16) | (self._payload[19] << 8) | self._payload[20])
            )/100
            self.mean_sea_level_altitude = self._signed_32bit(
                ((self._payload[21] << 24) | (self._payload[22] << 16) | (self._payload[23] << 8) | self._payload[24])
            )/100
            # Units according to AN0037 are in 1/100 scale (e.g. cm vs m)
            self.gdop = self._u16(25)/100
            self.pdop = self._u16(27)/100
            self.hdop = self._u16(29)/100
            self.vdop = self._u16(31)/100
            self.tdop = self._u16(33)/100
            self.ecef_x = self._signed_32bit(
                (self._payload[35] << 24) | (self._payload[36] << 16) | (self._payload[37] << 8) | self._payload[38]
            )/100
            self.ecef_y = self._signed_32bit(
                (self._payload[39] << 24) | (self._payload[40] << 16) | (self._payload[41] << 8) | self._payload[42]
            )/100
            self.ecef_z = self._signed_32bit(
                (self._payload[43] << 24) | (self._payload[44] << 16) | (self._payload[45] << 8) | self._payload[46]
            )/100
            self.ecef_vx = self._signed_32bit(
                (self._payload[47] << 24) | (self._payload[48] << 16) | (self._payload[49] << 8) | self._payload[50]
            )/100
            self.ecef_vy = self._signed_32bit(
                (self._payload[51] << 24) | (self._payload[52] << 16) | (self._payload[53] << 8) | self._payload[54]
            )/100
            self.ecef_vz = self._signed_32bit(
                (self._payload[55] << 24) | (self._payload[56] << 16) | (self._payload[57] << 8) | self._payload[58]
            )/100
            self.unix_time = self.gps_time_2_unix_time(self.week, self.tow)
            if self.debug:
                print('PRINTING NAV DATA PRINTING NAV DATA PRINTING NAV DATA ')
                self.print_nav_data()
            return True
        except Exception as e:
            print(f"Error parsing data: {e}")
            return False

    def parse_data_AN0030(self) -> bool:
        try:
            self.message_id = self._u8(0)
            self.IOD = self._u8(1)
            self.navigation_state = self._u8(2)
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
            self.GDOP = self._spfp(61)
            self.PDOP = self._spfp(65)
            self.HDOP = self._spfp(69)
            self.VDOP = self._spfp(73)
            self.TDOP = self._spfp(77)
            self.unix_time = self.gps_time_2_unix_time(self.week, self.tow)
            if self.debug:
                print('PRINTING NAV DATA PRINTING NAV DATA PRINTING NAV DATA ')
                self.print_nav_data()
            return True
        except Exception as e:
            print(f"Error parsing data: {e}")
            return False

    def _signed_32bit(self, value: int) -> int:
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
    def gps_time_2_unix_time(self, gps_week: int, tow: int) -> float:
        # Number of days in each month (non-leap year)
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

        # Helper function to check for leap years
        def is_leap_year(year):
            return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

        # Calculate the total number of days from GPS weeks
        total_days = gps_week * 7

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

        # Convert days to seconds
        unix_time = days_since_unix_epoch * 86400

        # Add TOW
        unix_time += tow

        # Calculate hours, minutes, and seconds
        seconds_in_day = unix_time % 86400
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

    # # TODO : Remove this method if it is not used anywhere
    # @property
    # def parsed_nav_data(self) -> dict:
    #     return self._parsed_data

    # def parse_fix_mode(self) -> int:
    #     if self._nav_data_hex["fix_mode"] == 0:
    #         if self.debug:
    #             self.data_strings["fix_mode"] = "No fix"
    #         return 0
    #     if self._nav_data_hex["fix_mode"] == 1:
    #         if self.debug:
    #             self.data_strings["fix_mode"] = "2D fix"
    #         return 1
    #     elif self._nav_data_hex["fix_mode"] == 2:
    #         if self.debug:
    #             self.data_strings["fix_mode"] = "3D fix"
    #         return 2
    #     else:
    #         if self.debug:
    #             self.data_strings["fix_mode"] = "3D + DGNSS fix"
    #         return 3

    # def parse_lat(self) -> int:
    #     lat_hex = self._nav_data_hex["latitude"]
    #     lat = lat_hex if lat_hex < 0x80000000 else lat_hex - 0x100000000
    #     if self.debug:
    #         # Convert from scale 1/1e-7 to decimal degrees
    #         latitude = lat * 1e-7

    #         # Determine North or South
    #         direction = "N" if latitude >= 0 else "S"
    #         latitude = abs(latitude)

    #         # Convert to degrees, minutes, and seconds
    #         degrees = int(latitude)
    #         minutes = int((latitude - degrees) * 60)
    #         seconds = (latitude - degrees - minutes / 60) * 3600

    #         # Format output
    #         self.data_strings["latitude"] = f"{degrees}° {minutes}' {seconds:.2f}\" {direction}"
    #     return lat

    # def parse_lon(self) -> int:
    #     lon_hex = self._nav_data_hex["longitude"]
    #     lon = lon_hex if lon_hex < 0x80000000 else lon_hex - 0x100000000
    #     if self.debug:
    #         # Convert raw longitude as signed 32-bit integer
    #         raw_longitude = lon
    #         if raw_longitude > 0x7FFFFFFF:  # Handle 32-bit signed conversion
    #             raw_longitude -= 0x100000000

    #         # Convert to decimal degrees
    #         longitude = raw_longitude / 1e7

    #         # Normalize longitude to -180 to 180 range (if needed)
    #         if longitude > 180:
    #             longitude -= 360

    #         # Determine East or West
    #         direction = "E" if longitude >= 0 else "W"
    #         longitude = abs(longitude)

    #         # Convert to degrees, minutes, and seconds
    #         degrees = int(longitude)
    #         minutes = int((longitude - degrees) * 60)
    #         seconds = (longitude - degrees - minutes / 60) * 3600

    #         # Format output
    #         self.data_strings["longitude"] = f"{degrees}° {minutes}' {seconds:.2f}\" {direction}"
    #     return lon

    # def parse_elip_alt(self) -> int:
    #     elip_alt_hex = self._nav_data_hex["ellipsoid_alt"]
    #     elip_alt = elip_alt_hex if elip_alt_hex < 0x80000000 else elip_alt_hex - 0x100000000
    #     if self.debug:
    #         # Convert from hundredths of a meter to meters
    #         distance_meters = elip_alt / 100

    #         # Format output
    #         self.data_strings["ellipsoid_alt"] = f"{distance_meters:.2f} m"
    #     return elip_alt

    # def parse_msl_alt(self) -> int:
    #     msl_alt_hex = self._nav_data_hex["mean_sea_lvl_alt"]
    #     msl_alt = msl_alt_hex if msl_alt_hex < 0x80000000 else msl_alt_hex - 0x100000000
    #     if self.debug:
    #         # Convert from hundredths of a meter to meters
    #         distance_meters = msl_alt / 100

    #         # Format output
    #         self.data_strings["mean_sea_lvl_alt"] = f"{distance_meters:.2f} m"
    #     return msl_alt

    # def parse_gdop(self) -> int:
    #     gdop = int(self._nav_data_hex["gdop"])
    #     if self.debug:
    #         self.data_strings["gdop"] = tempgdop
    #     return gdop

    # def parse_pdop(self) -> int:
    #     pdop = int(self._nav_data_hex["pdop"])
    #     if self.debug:
    #         self.data_strings["pdop"] = temp_pdop
    #     return pdop

    # def parse_hdop(self) -> int:
    #     hdop = int(self._nav_data_hex["hdop"])
    #     if self.debug:
    #         self.data_strings["hdop"] = temp_hdop
    #     return hdop

    # def parse_vdop(self) -> int:
    #     vdop = int(self._nav_data_hex["vdop"])
    #     if self.debug:
    #         self.data_strings["vdop"] = temp_vdop
    #     return vdop

    # def parse_tdop(self) -> int:
    #     tdop = int(self._nav_data_hex["tdop"])
    #     if self.debug:
    #         self.data_strings["tdop"] = temp_tdop
    #     return tdop

    # def parse_ecef_x(self) -> int:
    #     ecef_x_hex = self._nav_data_hex["ecef_x"]
    #     ecef_x = ecef_x_hex if ecef_x_hex < 0x80000000 else ecef_x_hex - 0x100000000
    #     if self.debug:

    #         # Format output
    #         self.data_strings["ecef_x"] = f"{distance_meters:.2f} m"
    #     return ecef_x

    # def parse_ecef_y(self) -> int:
    #     ecef_y_hex = self._nav_data_hex["ecef_y"]
    #     ecef_y = ecef_y_hex if ecef_y_hex < 0x80000000 else ecef_y_hex - 0x100000000
    #     if self.debug:

    #         # Format output
    #         self.data_strings["ecef_y"] = f"{distance_meters:.2f} m"
    #     return ecef_y

    # def parse_ecef_z(self) -> int:
    #     ecef_z_hex = self._nav_data_hex["ecef_z"]
    #     ecef_z = ecef_z_hex if ecef_z_hex < 0x80000000 else ecef_z_hex - 0x100000000
    #     if self.debug:

    #         # Format output
    #         self.data_strings["ecef_z"] = f"{distance_meters:.2f} m"
    #     return ecef_z

    # def parse_ecef_vx(self) -> int:
    #     ecef_vx_hex = self._nav_data_hex["ecef_vx"]
    #     ecef_vx = ecef_vx_hex if ecef_vx_hex < 0x80000000 else ecef_vx_hex - 0x100000000
    #     if self.debug:
    #         if self._board == "PX1120S":
    #             # Convert from hundredths of a meter/seconds to meters/seconds
    #             speed_meters = ecef_vx / 100

    #         # Format output
    #         self.data_strings["ecef_vx"] = f"{speed_meters:.2f} m/s"
    #     return ecef_vx

    # def parse_ecef_vy(self) -> int:
    #     ecef_vy_hex = self._nav_data_hex["ecef_vy"]
    #     ecef_vy = ecef_vy_hex if ecef_vy_hex < 0x80000000 else ecef_vy_hex - 0x100000000
    #     if self.debug:
    #         if self._board == "PX1120S":
    #             # Convert from hundredths of a meter/seconds to meters/seconds
    #             speed_meters = ecef_vy / 100

    #         # Format output
    #         self.data_strings["ecef_vy"] = f"{speed_meters:.2f} m/s"
    #     return ecef_vy

    # def parse_ecef_vz(self) -> int:
    #     ecef_vz_hex = self._nav_data_hex["ecef_vz"]
    #     ecef_vz = ecef_vz_hex if ecef_vz_hex < 0x80000000 else ecef_vz_hex - 0x100000000
    #     if self.debug:
    #         if self._board == "PX1120S":
    #             # Convert from hundredths of a meter/seconds to meters/seconds
    #             speed_meters = ecef_vz / 100

    #         # Format output
    #         self.data_strings["ecef_vz"] = f"{speed_meters:.2f} m/s"
    #     return ecef_vz

    # def print_parsed_strings(self):
    #     print("Parsed Message:")
    #     print("=" * 40)
    #     print(f"Message ID:                 {self.message_id}")
    #     print(f"Fix Mode:                   {self.data_strings.get('fix_mode', 'N/A')}")
    #     print(f"Number of Satellites:       {self.number_of_sv}")
    #     print(f"GPS Week:                   {self.week}")
    #     print(f"Time of Week:               {self.tow}")
    #     print(f"Latitude:                   {self.data_strings.get('latitude', 'N/A')}")
    #     print(f"Longitude:                  {self.data_strings.get('longitude', 'N/A')}")
    #     print(f"Ellipsoid Altitude:         {self.data_strings.get('ellipsoid_altitude', 'N/A')}")
    #     print(f"Mean Sea Level Altitude:    {self.data_strings.get('mean_sea_level_altitude', 'N/A')}")
    #     print(f"GDOP:                       {self.data_strings.get('gdop', 'N/A')}")
    #     print(f"PDOP:                       {self.data_strings.get('pdop', 'N/A')}")
    #     print(f"HDOP:                       {self.data_strings.get('hdop', 'N/A')}")
    #     print(f"VDOP:                       {self.data_strings.get('vdop', 'N/A')}")
    #     print(f"TDOP:                       {self.data_strings.get('tdop', 'N/A')}")
    #     print(f"ECEF X:                     {self.data_strings.get('ecef_x', 'N/A')}")
    #     print(f"ECEF Y:                     {self.data_strings.get('ecef_y', 'N/A')}")
    #     print(f"ECEF Z:                     {self.data_strings.get('ecef_z', 'N/A')}")
    #     print(f"ECEF Vx:                    {self.data_strings.get('ecef_vx', 'N/A')}")
    #     print(f"ECEF Vy:                    {self.data_strings.get('ecef_vy', 'N/A')}")
    #     print(f"ECEF Vz:                    {self.data_strings.get('ecef_vz', 'N/A')}")
    #     print("=" * 40)

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
                "navigation_state": self.navigation_state,
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
                "GDOP": self.GDOP,
                "PDOP": self.PDOP,
                "HDOP": self.HDOP,
                "VDOP": self.VDOP,
                "TDOP": self.TDOP,
                "unix_time": self.unix_time,
                "timestamp_utc": self.timestamp_utc,
            }
        return self._nav_data_hex

    def write(self, bytestr) -> Optional[int]:
        return self._uart.write(bytestr)

    def send_binary(self, bytestr) -> None:
        self.write(bytestr)

    # TODO : Change this so that it always sends the binary message rather than needing set on each run
    def set_to_binary(self) -> None:
        """Send Set to Binary Mode command (Message ID 0x09)."""
        self.write(b"\xa0\xa1\x00\x03\x09\x02\x00\x0b\x0d\x0a")
        # self.write(b"\xA0\xA1\x00\x04\x64\x2F\x01\x00\x4A\x0D\x0A")

    def query_binary_status(self) -> None:
        """Send Query Binary Status command (Message ID 0x1F)."""
        self.write(b"\xa0\xa1\x00\x01\x1F\x1F\x0d\x0a")

    def enable_periodic_nav_data(self) -> None:
        """Send Enable Periodic Navigation Data command (Message ID 0x11)."""
        self.write(b"\xa0\xa1\x00\x03\x11\x01\x00\x10\x0d\x0a")

    def disable_nmea_periodic(self) -> None:
        """Send Disable NMEA Periodic Messages command (Message ID 0x64)."""
        self.write(b"\xa0\xa1\x00\x0F\x64\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x67\x0d\x0a")

    def query_nav_data(self) -> None:
        """Send Query Navigation Data command (Message ID 0x10)."""
        # 0xA0 0xA1 = start, 0x00 0x01 = 1 byte payload, 0x10 = Query Nav Data, 0x10 = checksum, 0x0D 0x0A = end
        self.write(b"\xa0\xa1\x00\x01\x10\x10\x0d\x0a") # This queries the wrong thing!

    def reset_to_factory_defaults(self) -> None:
        """Send Reset to Factory Defaults command (Message ID 0x04)."""
        self.write(b"\xa0\xa1\x00\x02\x04\x00\x04\x0d\x0a")

    def disable_unnecessary_binary_data(self) -> None:
        """Send Disable Unecessary Nav Binary Messages command (Message ID 0x1E)."""
        self.write(b"\xa0\xa1\x00\x09\x1e\x00\x00\x00\x00\x01\x03\x00\x00\x1c\x0d\x0a")

    @property
    def in_waiting(self) -> int:
        return self._uart.in_waiting
 
    def readline(self) -> Optional[bytes]:
        return self._uart.readline()

    def read(self, nbytes: int) -> Optional[bytes]:
        return self._uart.read(nbytes)

    def _read_sentence(self) -> Optional[bytes]:
        # Need at least 65 bytes for nav data message: 2 start + 2 len + 59 payload + 1 cs + 2 end = 66
        # But we check for header first        

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
