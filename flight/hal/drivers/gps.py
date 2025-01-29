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
    def __init__(self, uart: UART, enable=None, debug: bool = False, mock: bool = True) -> None:
        self._uart = uart
        self.debug = debug
        self._msg = None
        self._payload_len = 0
        self._msg_id = 0
        self._msg_cs = 0
        self._payload = bytearray([0] * 59)
        self._nav_data_hex = {}  # Navigation data as a dictionary of hex values

        if self.debug:
            self.data_strings = {  # Navigation data as a dictionary of strings for debugging
                "message_id": "None",
                "fix_mode": "None",
                "number_of_sv": "None",
                "gps_week": "None",
                "tow": "None",
                "latitude": "None",
                "longitude": "None",
                "ellipsoid_alt": "None",
                "mean_sea_lvl_alt": "None",
                "gdop": "None",
                "pdop": "None",
                "hdop": "None",
                "vdop": "None",
                "tdop": "None",
                "ecef_x": "None",
                "ecef_y": "None",
                "ecef_z": "None",
                "ecef_vx": "None",
                "ecef_vy": "None",
                "ecef_vz": "None",
            }

        # TODO: Check the formats of these values as used in the FSW
        # Initialize null starting values for all GPS data
        # These values are used for logging and will be ints
        self.timestamp_utc = None  # UTC as a dictionary in the form {year, month, day, hour, minute, second}
        self.unix_time = None  # Unix time in seconds
        self.message_id = None  # Message ID
        self.fix_mode = None  # Fix mode as an int
        self.number_of_sv = None  # Number of satellites used in the solution
        self.week = None  # The number of weeks since the GPS epoch
        self.tow = None  # Time of week in 1/100 seconds
        self.latitude = None  # Latitude as a signed int
        self.longitude = None  # Longitude as a signed int
        self.ellipsoid_altitude = None  # Ellipsoid altitude in 1/100 meters
        self.mean_sea_level_altitude = None  # Mean sea level altitude in 1/100 meters
        self.gdop = None  # Geometric dilution of precision in 1/100
        self.pdop = None  # Position dilution of precision in 1/100
        self.hdop = None  # Horizontal dilution of precision in 1/100
        self.vdop = None  # Vertical dilution of precision in 1/100
        self.tdop = None  # Time dilution of precision in 1/100
        self.ecef_x = None  # ECEF X coordinate in 1/100 meters
        self.ecef_y = None  # ECEF Y coordinate in 1/100 meters
        self.ecef_z = None  # ECEF Z coordinate in 1/100 meters
        self.ecef_vx = None  # ECEF X velocity in 1/100 meters per second
        self.ecef_vy = None  # ECEF Y velocity in 1/100 meters per second
        self.ecef_vz = None  # ECEF Z velocity in 1/100 meters per second

        # Don't care to enable the GPS module during initialization
        self._enable = enable
        if self._enable is not None:
            self._enable = DigitalInOut(enable)
            self._enable.switch_to_output()
            self._enable = False

        # TODO : This needs to be removed for any infield testing
        self.mock = mock
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
        if self.mock:
            msg = self.mock_message
        else:
            try:
                msg = self._parse_sentence()
            except UnicodeError:
                return False
            if msg is None or len(msg) < 11:
                return False

        if self.debug:
            if self.mock:
                print("Mock message: \n", self.mock_message)
            else:
                print("Raw message: \n", msg)

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
            print("Payload: \n", self._payload)

        cs = 0
        for i in self._payload:
            cs ^= i
        if cs != self._msg_cs:
            if self.debug:
                print("Checksum failed!")
            return False

        # Populate _nav_data_hex as a dictionary
        self._nav_data_hex = {
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
            for key, value in self._nav_data_hex.items():
                print(f"{str(key)}: {value}")
            print("=" * 40)

        self.parse_data()

        return True

    # TODO : Remove this method if it is not used anywhere
    @property
    def parsed_nav_data(self) -> dict:
        return self._parsed_data

    def parse_fix_mode(self) -> int:
        if self._nav_data_hex["fix_mode"] == 0:
            if self.debug:
                self.data_strings["fix_mode"] = "No fix"
            return 0
        if self._nav_data_hex["fix_mode"] == 1:
            if self.debug:
                self.data_strings["fix_mode"] = "2D fix"
            return 1
        elif self._nav_data_hex["fix_mode"] == 2:
            if self.debug:
                self.data_strings["fix_mode"] = "3D fix"
            return 2
        else:
            if self.debug:
                self.data_strings["fix_mode"] = "3D + DGNSS fix"
            return 3

    def has_fix(self) -> bool:
        """True if a current fix for location information is available."""
        if self._nav_data_hex["fix_mode"] is not None and self._nav_data_hex["fix_mode"] >= 1:
            return True
        else:
            return False

    def has_3d_fix(self) -> bool:
        """Returns true if there is a 3d fix available.
        use has_fix to determine if a 2d fix is available,
        passing it the same data"""
        return self._nav_data_hex["fix_mode"] is not None and self._nav_data_hex["fix_mode"] >= 2

    def parse_lat(self) -> int:
        lat_hex = self._nav_data_hex["latitude"]
        lat = lat_hex if lat_hex < 0x80000000 else lat_hex - 0x100000000
        if self.debug:
            # Convert from scale 1/1e-7 to decimal degrees
            latitude = lat * 1e-7

            # Determine North or South
            direction = "N" if latitude >= 0 else "S"
            latitude = abs(latitude)

            # Convert to degrees, minutes, and seconds
            degrees = int(latitude)
            minutes = int((latitude - degrees) * 60)
            seconds = (latitude - degrees - minutes / 60) * 3600

            # Format output
            self.data_strings["latitude"] = f"{degrees}° {minutes}' {seconds:.2f}\" {direction}"
        return lat

    def parse_lon(self) -> int:
        lon_hex = self._nav_data_hex["longitude"]
        lon = lon_hex if lon_hex < 0x80000000 else lon_hex - 0x100000000
        if self.debug:
            # Convert raw longitude as signed 32-bit integer
            raw_longitude = lon
            if raw_longitude > 0x7FFFFFFF:  # Handle 32-bit signed conversion
                raw_longitude -= 0x100000000

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
            self.data_strings["longitude"] = f"{degrees}° {minutes}' {seconds:.2f}\" {direction}"
        return lon

    def parse_elip_alt(self) -> int:
        elip_alt_hex = self._nav_data_hex["ellipsoid_alt"]
        elip_alt = elip_alt_hex if elip_alt_hex < 0x80000000 else elip_alt_hex - 0x100000000
        if self.debug:
            # Convert from hundredths of a meter to meters
            distance_meters = elip_alt / 100

            # Format output
            self.data_strings["ellipsoid_alt"] = f"{distance_meters:.2f} m"
        return elip_alt

    def parse_msl_alt(self) -> int:
        msl_alt_hex = self._nav_data_hex["mean_sea_lvl_alt"]
        msl_alt = msl_alt_hex if msl_alt_hex < 0x80000000 else msl_alt_hex - 0x100000000
        if self.debug:
            # Convert from hundredths of a meter to meters
            distance_meters = msl_alt / 100

            # Format output
            self.data_strings["mean_sea_lvl_alt"] = f"{distance_meters:.2f} m"
        return msl_alt

    def parse_gdop(self) -> int:
        gdop = int(self._nav_data_hex["gdop"])
        if self.debug:
            # Convert from hundredths to decimal
            temp_gdop = gdop * 0.01
            self.data_strings["gdop"] = temp_gdop
        return gdop

    def parse_pdop(self) -> int:
        pdop = int(self._nav_data_hex["pdop"])
        if self.debug:
            # Convert from hundredths to decimal
            temp_pdop = pdop * 0.01
            self.data_strings["pdop"] = temp_pdop
        return pdop

    def parse_hdop(self) -> int:
        hdop = int(self._nav_data_hex["hdop"])
        if self.debug:
            # Convert from hundredths to decimal
            temp_hdop = hdop * 0.01
            self.data_strings["hdop"] = temp_hdop
        return hdop

    def parse_vdop(self) -> int:
        vdop = int(self._nav_data_hex["vdop"])
        if self.debug:
            # Convert from hundredths to decimal
            temp_vdop = vdop * 0.01
            self.data_strings["vdop"] = temp_vdop
        return vdop

    def parse_tdop(self) -> int:
        tdop = int(self._nav_data_hex["tdop"])
        if self.debug:
            # Convert from hundredths to decimal
            temp_tdop = tdop * 0.01
            self.data_strings["tdop"] = temp_tdop
        return tdop

    def parse_ecef_x(self) -> int:
        ecef_x_hex = self._nav_data_hex["ecef_x"]
        ecef_x = ecef_x_hex if ecef_x_hex < 0x80000000 else ecef_x_hex - 0x100000000
        if self.debug:
            # Convert from hundredths of a meter to meters
            distance_meters = ecef_x / 100

            # Format output
            self.data_strings["ecef_x"] = f"{distance_meters:.2f} m"
        return ecef_x

    def parse_ecef_y(self) -> int:
        ecef_y_hex = self._nav_data_hex["ecef_y"]
        ecef_y = ecef_y_hex if ecef_y_hex < 0x80000000 else ecef_y_hex - 0x100000000
        if self.debug:
            # Convert from hundredths of a meter to meters
            distance_meters = ecef_y / 100

            # Format output
            self.data_strings["ecef_y"] = f"{distance_meters:.2f} m"
        return ecef_y

    def parse_ecef_z(self) -> int:
        ecef_z_hex = self._nav_data_hex["ecef_z"]
        ecef_z = ecef_z_hex if ecef_z_hex < 0x80000000 else ecef_z_hex - 0x100000000
        if self.debug:
            # Convert from hundredths of a meter to meters
            distance_meters = ecef_z / 100

            # Format output
            self.data_strings["ecef_z"] = f"{distance_meters:.2f} m"
        return ecef_z

    def parse_ecef_vx(self) -> int:
        ecef_vx_hex = self._nav_data_hex["ecef_vx"]
        ecef_vx = ecef_vx_hex if ecef_vx_hex < 0x80000000 else ecef_vx_hex - 0x100000000
        if self.debug:
            # Convert from hundredths of a meter to meters
            speed_meters = ecef_vx / 100

            # Format output
            self.data_strings["ecef_vx"] = f"{speed_meters:.2f} m/s"
        return ecef_vx

    def parse_ecef_vy(self) -> int:
        ecef_vy_hex = self._nav_data_hex["ecef_vy"]
        ecef_vy = ecef_vy_hex if ecef_vy_hex < 0x80000000 else ecef_vy_hex - 0x100000000
        if self.debug:
            # Convert from hundredths of a meter to meters
            speed_meters = ecef_vy / 100

            # Format output
            self.data_strings["ecef_vy"] = f"{speed_meters:.2f} m/s"
        return ecef_vy

    def parse_ecef_vz(self) -> int:
        ecef_vz_hex = self._nav_data_hex["ecef_vz"]
        ecef_vz = ecef_vz_hex if ecef_vz_hex < 0x80000000 else ecef_vz_hex - 0x100000000
        if self.debug:
            # Convert from hundredths of a meter to meters
            speed_meters = ecef_vz / 100

            # Format output
            self.data_strings["ecef_vz"] = f"{speed_meters:.2f} m/s"
        return ecef_vz

    def gps_datetime(self, gps_week: int, tow: int) -> int:
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
        self.unix_time = int(days_since_unix_epoch) * int(86400)

        # Add TOW (convert from 1/100 sec to seconds)
        self.unix_time += tow / 100

        # Calculate hours, minutes, and seconds
        seconds_in_day = self.unix_time % 86400
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
        return self.unix_time

    def parse_data(self) -> dict:
        if not self._nav_data_hex:
            return
        self.message_id = self._nav_data_hex["message_id"]
        self.fix_mode = self.parse_fix_mode()
        self.number_of_sv = int(self._nav_data_hex["number_of_sv"])
        self.week = int(self._nav_data_hex["gps_week"])
        self.tow = int(self._nav_data_hex["tow"])
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
        self.timestamp_utc = self.gps_datetime(self.week, self.tow)

    def print_parsed_strings(self):
        print("Parsed Message:")
        print("=" * 40)
        print(f"Message ID:                 {self.message_id}")
        print(f"Fix Mode:                   {self.data_strings.get('fix_mode', 'N/A')}")
        print(f"Number of Satellites:       {self.number_of_sv}")
        print(f"GPS Week:                   {self.week}")
        print(f"Time of Week:               {self.tow}")
        print(f"Latitude:                   {self.data_strings.get('latitude', 'N/A')}")
        print(f"Longitude:                  {self.data_strings.get('longitude', 'N/A')}")
        print(f"Ellipsoid Altitude:         {self.data_strings.get('ellipsoid_altitude', 'N/A')}")
        print(f"Mean Sea Level Altitude:    {self.data_strings.get('mean_sea_level_altitude', 'N/A')}")
        print(f"GDOP:                       {self.data_strings.get('gdop', 'N/A')}")
        print(f"PDOP:                       {self.data_strings.get('pdop', 'N/A')}")
        print(f"HDOP:                       {self.data_strings.get('hdop', 'N/A')}")
        print(f"VDOP:                       {self.data_strings.get('vdop', 'N/A')}")
        print(f"TDOP:                       {self.data_strings.get('tdop', 'N/A')}")
        print(f"ECEF X:                     {self.data_strings.get('ecef_x', 'N/A')}")
        print(f"ECEF Y:                     {self.data_strings.get('ecef_y', 'N/A')}")
        print(f"ECEF Z:                     {self.data_strings.get('ecef_z', 'N/A')}")
        print(f"ECEF Vx:                    {self.data_strings.get('ecef_vx', 'N/A')}")
        print(f"ECEF Vy:                    {self.data_strings.get('ecef_vy', 'N/A')}")
        print(f"ECEF Vz:                    {self.data_strings.get('ecef_vz', 'N/A')}")
        print("=" * 40)

    def get_nav_data(self) -> dict:
        """Returns the current navigation data as a dictionary."""
        return self._nav_data_hex

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
