try:
    import time
    from typing import Optional

    from busio import UART
    from digitalio import DigitalInOut
    from hal.drivers.middleware.errors import Errors

    # from hal.drivers.middleware.generic_driver import Driver
    from micropython import const
except ImportError:
    pass


EPOCH_YEAR = 1980
EPOCH_MONTH = 1
EPOCH_DAY = 5


class GPS:
    def __init__(self, uart: UART, enable=None, debug: bool = False) -> None:
        self._uart = uart
        self.debug = debug
        self._msg = None
        self._payload_len = 0
        self._msg_id = 0
        self._msg_cs = 0
        self._payload = bytearray([0] * 59)
        self._nav_data = {}

        # TODO: Check the formats of these values as used in the FSW
        # Initialize null starting values for GPS attributes
        self.timestamp_utc = None  # UTC as a dictionary in the form {year, month, day, hour, minute, second}
        self.message_id = None  # Message ID
        self.fix_mode = None  # Fix mode as a text string
        self.number_of_sv = None  # Number of satellites used in the solution
        self.week = None  # The number of weeks since the GPS epoch
        self.tow = None  # Time of week in 1/100 seconds [TODO: Check this]
        self.latitude = None  # Latitude as a text string
        self.longitude = None  # Longitude as a text string
        self.ellipsoid_altitude = None  # Ellipsoid altitude in meters
        self.mean_sea_level_altitude = None  # Mean sea level altitude in meters
        self.gdop = None  # Geometric dilution of precision
        self.pdop = None  # Position dilution of precision
        self.hdop = None  # Horizontal dilution of precision
        self.vdop = None  # Vertical dilution of precision
        self.tdop = None  # Time dilution of precision
        self.ecef_x = None  # ECEF X coordinate in meters
        self.ecef_y = None  # ECEF Y coordinate in meters
        self.ecef_z = None  # ECEF Z coordinate in meters
        self.ecef_vx = None  # ECEF X velocity in meters per second
        self.ecef_vy = None  # ECEF Y velocity in meters per second
        self.ecef_vz = None  # ECEF Z velocity in meters per second

        # Don't care to enable the GPS module during initialization
        self._enable = enable
        if self._enable is not None:
            self._enable = DigitalInOut(enable)
            self._enable.switch_to_output()
            self._enable = False

        # TODO : This needs to be removed for any infield testing
        self.mock = True
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
        try:
            msg = self._parse_sentence()
        except UnicodeError:
            return False
        if msg is None or len(msg) < 11:
            return False

        if self.debug:
            print(msg)

        if self.mock:
            msg = self.mock_message
            print("Mock message: /n", msg)

        self._msg = [hex(i) for i in msg]
        self._payload_len = ((msg[2] & 0xFF) << 8) | msg[3]
        self._msg_id = msg[4]
        self._msg_cs = msg[-3]
        self._payload = bytearray(int(i, 16) for i in self._msg[4:-3])

        if self._msg_id != 0xA8:
            if self.debug:
                print("Invalid message ID, expected 0xA8, got: ", hex(self._msg_id))
            return False

        if self._payload_len != 59:
            if self.debug:
                print("Invalid payload length, expected 59, got: ", self._payload_len)
            return False

        if self.debug:
            print("Raw message: \n", self._msg)
            print("Payload: \n", self._payload)

        cs = 0
        for i in self._payload:
            cs ^= i
        if cs != self._msg_cs:
            if self.debug:
                print("Checksum failed!")
            return False

        # Populate _nav_data as a dictionary
        self._nav_data = {
            "message_id": self._payload[0],
            "fix_mode": self._payload[1],
            "number_of_sv": self._payload[2],
            "gps_week": (self._payload[3] << 8) | self._payload[4],
            "tow": (self._payload[5] << 24) | (self._payload[6] << 16) | (self._payload[7] << 8) | self._payload[8],
            "latitude": (self._payload[9] << 24) | (self._payload[10] << 16) | (self._payload[11] << 8) | self._payload[12],
            "longitude": (self._payload[13] << 24) | (self._payload[14] << 16) | (self._payload[15] << 8) | self._payload[16],
            "ellipsoid_alt": (self._payload[17] << 24)
            | (self._payload[18] << 16)
            | (self._payload[19] << 8)
            | self._payload[20],
            "mean_sea_lvl_alt": (self._payload[21] << 24)
            | (self._payload[22] << 16)
            | (self._payload[23] << 8)
            | self._payload[24],
            "gdop": (self._payload[25] << 8) | self._payload[26],
            "pdop": (self._payload[27] << 8) | self._payload[28],
            "hdop": (self._payload[29] << 8) | self._payload[30],
            "vdop": (self._payload[31] << 8) | self._payload[32],
            "tdop": (self._payload[33] << 8) | self._payload[34],
            "ecef_x": (self._payload[35] << 24) | (self._payload[36] << 16) | (self._payload[37] << 8) | self._payload[38],
            "ecef_y": (self._payload[39] << 24) | (self._payload[40] << 16) | (self._payload[41] << 8) | self._payload[42],
            "ecef_z": (self._payload[43] << 24) | (self._payload[44] << 16) | (self._payload[45] << 8) | self._payload[46],
            "ecef_vx": (self._payload[47] << 24) | (self._payload[48] << 16) | (self._payload[49] << 8) | self._payload[50],
            "ecef_vy": (self._payload[51] << 24) | (self._payload[52] << 16) | (self._payload[53] << 8) | self._payload[54],
            "ecef_vz": (self._payload[55] << 24) | (self._payload[56] << 16) | (self._payload[57] << 8) | self._payload[58],
        }

        # Print the navigation data if debug is enabled line by line:
        if self.debug:
            print("~~~~DEBUG~~~~")
            print("Navigation Data:")
            print("=" * 40)
            for key, value in self._nav_data.items():
                print(f"{str(key)}: {value}")
            print("=" * 40)

        self.parse_data()

        return True

    @property
    def parsed_nav_data(self) -> dict:
        return self._parsed_data

    def parse_fix_mode(self) -> str:
        if self._nav_data["fix_mode"] == 0:
            return "No fix"
        if self._nav_data["fix_mode"] == 1:
            return "2D fix"
        elif self._nav_data["fix_mode"] == 2:
            return "3D fix"
        else:
            return "3D + DGNSS fix"

    def has_fix(self):
        """True if a current fix for location information is available."""
        return self._nav_data["fix_mode"] is not None and self._nav_data["fix_mode"] >= 1

    def has_3d_fix(self):
        """Returns true if there is a 3d fix available.
        use has_fix to determine if a 2d fix is available,
        passing it the same data"""
        return self._nav_data["fix_mode"] is not None and self._nav_data["fix_mode"] >= 2

    def parse_lat(self) -> str:
        # Convert from scale 1/1e-7 to decimal degrees
        latitude = self._nav_data["latitude"] * 1e-7

        # Determine North or South
        direction = "N" if latitude >= 0 else "S"
        latitude = abs(latitude)

        # Convert to degrees, minutes, and seconds
        degrees = int(latitude)
        minutes = int((latitude - degrees) * 60)
        seconds = (latitude - degrees - minutes / 60) * 3600

        # Format output
        latitude_str = f"{degrees}° {minutes}' {seconds:.2f}\" {direction}"
        return latitude_str

    def parse_lon(self) -> str:
        # Convert raw longitude as signed 32-bit integer
        raw_longitude = self._nav_data["longitude"]
        if raw_longitude > 0x7FFFFFFF:  # Handle 32-bit signed conversion
            raw_longitude -= 0x100000000

        if self.debug:
            print("Raw Longitude:", raw_longitude)

        # Convert to decimal degrees
        longitude = raw_longitude / 1e7

        # Normalize longitude to -180 to 180 range (if needed)
        if longitude > 180:
            longitude -= 360

        # Determine East or West
        direction = "E" if longitude >= 0 else "W"
        longitude = abs(longitude)

        # Convert to degrees, minutes, and seconds
        degrees = int(longitude)
        minutes = int((longitude - degrees) * 60)
        seconds = (longitude - degrees - minutes / 60) * 3600

        # Format output
        longitude_str = f"{degrees}° {minutes}' {seconds:.2f}\" {direction}"
        return longitude_str

    def parse_elip_alt(self) -> float:
        # Convert from hundredths of a meter to meters
        distance_meters = self._nav_data["ellipsoid_alt"] / 100

        # Format output
        distance_str = f"{distance_meters:.2f} m"
        return distance_str

    def parse_msl_alt(self) -> float:
        # Convert from hundredths of a meter to meters
        distance_meters = self._nav_data["mean_sea_lvl_alt"] / 100

        # Format output
        distance_str = f"{distance_meters:.2f} m"
        return distance_str

    def parse_gdop(self) -> float:
        return self._nav_data["gdop"] * 0.01

    def parse_pdop(self) -> float:
        return self._nav_data["pdop"] * 0.01

    def parse_hdop(self) -> float:
        return self._nav_data["hdop"] * 0.01

    def parse_vdop(self) -> float:
        return self._nav_data["vdop"] * 0.01

    def parse_tdop(self) -> float:
        return self._nav_data["tdop"] * 0.01

    def parse_ecef_x(self) -> float:
        # Convert from hundredths of a meter to meters
        distance_meters = self._nav_data["ecef_x"] / 100

        # Format output
        distance_str = f"{distance_meters:.2f} m"
        return distance_str

    def parse_ecef_y(self) -> float:
        # Convert from hundredths of a meter to meters
        distance_meters = self._nav_data["ecef_y"] / 100

        # Format output
        distance_str = f"{distance_meters:.2f} m"
        return distance_str

    def parse_ecef_z(self) -> float:
        # Convert from hundredths of a meter to meters
        distance_meters = self._nav_data["ecef_z"] / 100

        # Format output
        distance_str = f"{distance_meters:.2f} m"
        return distance_str

    def parse_ecef_vx(self) -> float:
        # Convert from hundredths of a meter to meters
        speed_meters = self._nav_data["ecef_vx"] / 100

        # Format output
        speed_meters = f"{speed_meters:.2f} m/s"
        return speed_meters

    def parse_ecef_vy(self) -> float:
        # Convert from hundredths of a meter to meters
        speed_meters = self._nav_data["ecef_vy"] / 100

        # Format output
        speed_meters = f"{speed_meters:.2f} m/s"
        return speed_meters

    def parse_ecef_vz(self) -> float:
        # Convert from hundredths of a meter to meters
        speed_meters = self._nav_data["ecef_vz"] / 100

        # Format output
        speed_meters = f"{speed_meters:.2f} m/s"
        return speed_meters

    def gps_datetime(self, gps_week: int, tow: int) -> dict:
        """Get the date and time as a dictionary from GPS week and TOW (time of week in 1/100 seconds)."""

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
        unix_time = int(days_since_unix_epoch) * int(86400)

        # Add TOW (convert from 1/100 sec to seconds)
        print("TOW:", tow)
        unix_time += tow / 100

        # Calculate hours, minutes, and seconds
        seconds_in_day = unix_time % 86400
        hours = int(seconds_in_day // 3600)
        minutes = int((seconds_in_day % 3600) // 60)
        seconds = seconds_in_day % 60

        if self.debug:
            print("Year:    ", year)
            print("Month:   ", month)
            print("Day:     ", day)
            print("Hours:   ", hours)
            print("Minutes: ", minutes)
            print("Seconds: ", seconds)

        # Return the date and time as a dictionary
        return {"year": year, "month": month, "day": day, "hour": hours, "minute": minutes, "second": round(seconds, 2)}

    def parse_data(self) -> dict:
        if not self._nav_data:
            return
        self.message_id = self._nav_data["message_id"]
        self.fix_mode = self.parse_fix_mode()
        self.number_of_sv = self._nav_data["number_of_sv"]
        self.week = self._nav_data["gps_week"]
        self.tow = self._nav_data["tow"]
        self.latitude = self.parse_lat()
        self.longitude = self.parse_lon()
        self.ellipsoid_altitude = self.parse_elip_alt()
        self.mean_sea_level_altitude = self.parse_msl_alt()
        self.gdop = self.parse_gdop()
        self.pdop = self.parse_pdop()
        self.hdop = self.parse_hdop()
        self.vdop = self.parse_vdop()
        self.tdop = self.parse_tdop()
        self.ecef_x = self.parse_ecef_x()
        self.ecef_y = self.parse_ecef_y()
        self.ecef_z = self.parse_ecef_z()
        self.ecef_vx = self.parse_ecef_vx()
        self.ecef_vy = self.parse_ecef_vy()
        self.ecef_vz = self.parse_ecef_vz()
        self.timestamp_utc = self.gps_datetime(self.week, self._nav_data["tow"])

    def print_parsed_msg(self):
        print("Parsed Message:")
        print("=" * 40)
        print(f"Message ID:                 {self.message_id}")
        print(f"Fix Mode:                   {self.fix_mode}")
        print(f"Number of Satellites:       {self.number_of_sv}")
        print(f"GPS Week:                   {self.week}")
        print(f"Time of Week:               {self.tow}")
        print(f"Latitude:                   {self.latitude}")
        print(f"Longitude:                  {self.longitude}")
        print(f"Ellipsoid Altitude:         {self.ellipsoid_altitude}")
        print(f"Mean Sea Level Altitude:    {self.mean_sea_level_altitude}")
        print(f"GDOP:                       {self.gdop}")
        print(f"PDOP:                       {self.pdop}")
        print(f"HDOP:                       {self.hdop}")
        print(f"VDOP:                       {self.vdop}")
        print(f"TDOP:                       {self.tdop}")
        print(f"ECEF X:                     {self.ecef_x}")
        print(f"ECEF Y:                     {self.ecef_y}")
        print(f"ECEF Z:                     {self.ecef_z}")
        print(f"ECEF Vx:                    {self.ecef_vx}")
        print(f"ECEF Vy:                    {self.ecef_vy}")
        print(f"ECEF Vz:                    {self.ecef_vz}")
        print(
            f"Timestamp (UTC):            {self.timestamp_utc.get('year')}-{self.timestamp_utc.get('month')}-",
            f"{self.timestamp_utc.get('day')} {self.timestamp_utc.get('hour')}:",
            f"{self.timestamp_utc.get('minute')}:{self.timestamp_utc.get('second')}",
        )
        print("=" * 40)

    def get_nav_data(self) -> dict:
        """Returns the current navigation data as a dictionary."""
        return self._nav_data

    def write(self, bytestr) -> Optional[int]:
        return self._uart.write(bytestr)

    def send_binary(self, bytestr) -> None:
        self.write(bytestr)

    # TODO : Change this so that it always sends the binary message rather than needing set on each run
    def set_to_binary(self) -> None:
        self.write(b"\xA0\xA1\x00\x03\x09\x02\x00\x0B\x0D\x0A")

    @property
    def in_waiting(self) -> int:
        return self._uart.in_waiting

    def readline(self) -> Optional[bytes]:
        return self._uart.readline()

    def _read_sentence(self) -> Optional[bytes]:
        if self.in_waiting < 11:
            return None
        return self.readline()

    def _parse_sentence(self) -> Optional[bytes]:
        return self._read_sentence()

    # TODO : Implement the enable and disable methods
    # TODO : CHeck if this is still possible on new board
    def enable(self) -> None:
        """Enable the GPS module through the enable pin"""
        self.__enable = True

    def disable(self) -> None:
        """Disable the GPS module through the enable pin"""
        self.__enable = False

    """
    ----------------------- HANDLER METHODS -----------------------
    """

    def get_flags(self):
        return {}

    ######################### DIAGNOSTICS #########################

    def __check_for_updates(self) -> int:
        """_check_for_errors: Checks for an update on the GPS

        :return: true if test passes, false if fails
        """
        num_tries = const(10)

        for i in range(num_tries):
            success = False

            success = self.update()
            if success:
                return Errors.NOERROR

            time.sleep(1)

        return Errors.GPS_UPDATE_CHECK_FAILED

    def run_diagnostics(self) -> list[int] | None:
        """run_diagnostic_test: Run all tests for the component

        :return: List of error codes
        """
        error_list = []

        error_list.append(self.__check_for_updates())

        error_list = list(set(error_list))

        if Errors.NOERROR not in error_list:
            self.errors_present = True

        return error_list
