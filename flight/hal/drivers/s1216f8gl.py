"""
Author: Chase Dunaway
Description: GPS Driver for the SkyTraq S1216F8-GL Module

This driver is designed to interface with the S1216F8-GL GPS modules over
UART using their binary protocol. It handles board detection, message parsing, and data extraction for navigation information.

Note, S1216F8-GL uses the AN0028 and AN0030 binary protocol.
"""

try:
    import struct
    from typing import Optional

    from busio import UART
    from digitalio import DigitalInOut, Direction
except ImportError:
    pass

try:
    from core import logger
except ImportError:
    logger = None


EPOCH_YEAR = 1980
EPOCH_MONTH = 1
EPOCH_DAY = 6
_FRAME_START = b"\xA0\xA1"
_FRAME_END = b"\x0D\x0A"
_MIN_FRAME_LEN = 8
_MAX_FRAME_PAYLOAD_LEN = 256
_MAX_RX_BUFFER_LEN = 4096
_RX_BUFFER_WARN_FRACTION = 4  # Warn if buffer is 1/{this value} of max length
_GPS_UTC_OFFSET_SECONDS = 18  # GPS Counts leap seconds, there are 18 as of June 2026


class GPS:
    def __init__(self, uart: UART, enable=None, debug: bool = False, rx_buffer_size: Optional[int] = None) -> None:
        self._uart = uart
        self._debug = debug
        if rx_buffer_size is None or int(rx_buffer_size) < _MIN_FRAME_LEN:
            self._max_rx_buffer_len = _MAX_RX_BUFFER_LEN
        else:
            self._max_rx_buffer_len = int(rx_buffer_size)
        self._enable = (
            None  # Enable pin is only used on older ARGUS boards, this does nothing but is a papertrail for deinit in HAL
        )
        if enable is not None:
            self._enable = DigitalInOut(enable)
            self._enable.direction = Direction.OUTPUT
            self._enable.value = True

        ################################################
        # BOARD PROTOCOL OUTPUT VARIABLES
        ################################################

        self._ordered_keys = [
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
            "gdop",
            "pdop",
            "hdop",
            "vdop",
            "tdop",
            "unix_time",
            "timestamp_utc",
        ]

        ################################################
        # MESSAGE OUTPUT
        ################################################

        # Payload Buffer:
        self._payload = bytearray([0] * 81)

        # Message Variables
        self._msg = None
        self._payload_len = 0
        self._msg_id = 0
        self._msg_cs = 0
        self.last_update_status = None
        self._rx_buffer = bytearray()

        ################################################
        # HELPER FLAGS
        ################################################

        # Helper Flags for Receiver Hardware Configuration
        # Setting to True will run the configuration function once
        self._RESET_TO_FACTORY = False
        self._BINARY_SET_FLAG = True  # MUST ALWAYS BE TRUE for the S1216F8-GL
        self._QUERIED_BINARY_STATUS_FLAG = False
        self._PERIODIC_NAV_FLAG = True  # MUST ALWAYS BE TRUE for the S1216F8-GL
        self._DISABLE_NMEA_FLAG = True  # MUST BE TRUE
        self._DISABLE_UNNECESSARY_BINARY_FLAG = True  # MUST BE TRUE

        ################################################
        # INITIALIZE GPS DATA FIELDS
        ################################################

        # These values are used for logging and will be ints
        self.timestamp_utc = None  # UTC as a dictionary in the form {year, month, day, hour, minute, second}

        self.unix_time = 0  # Unix time in whole seconds, type: int, unit: seconds

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

    ######################## MAIN LOOP ########################

    def update(self) -> bool:
        self.last_update_status = None

        ## CONFIGURE THE RECEIVER (Once-per-cycle flags)
        self._use_helper_functions()

        if not self._collect_message():
            return False

        if not self._parse_message_header():
            return False

        if not self._check_payload_and_ack():
            return False

        if not self._check_nav_data():
            return False

        if not self._checksum():
            return False

        return self._parse_nav_data()

    def _log(self, level: str, msg: str) -> None:
        if logger is None:
            return
        getattr(logger, level)(f"[GPS] {msg}")

    def _collect_message(self) -> bool:
        try:
            self._msg = self.read_sentence()
        except UnicodeError:
            self.last_update_status = "Unicode error when parsing GPS message"
            return False

        if self._msg is None:
            self.last_update_status = "GPS message is None"
            return False

        if len(self._msg) < 7:
            self.last_update_status = f"GPS message too short: {len(self._msg)} bytes"
            return False

        # Print the raw messages
        if self._debug:
            self._log("debug", "RAW")
            self._log("debug", str(self._msg))
            self._log("debug", "DECODE")
            self._log("debug", " ".join(f"{b:02x}" for b in self._msg))
        return True

    def _parse_message_header(self) -> bool:
        try:
            self._payload_len = int(((self._msg[2] & 0xFF) << 8) | self._msg[3])
            self._msg_id = int(self._msg[4])
            self._msg_cs = int(self._msg[-3])
            self._payload = bytearray(self._msg[4:-3])  # TODO Is this required
            return True
        except Exception as e:
            self.last_update_status = f"Error parsing message length, ID, checksum, or payload: {e}"
            return False

    def _check_payload_and_ack(self) -> bool:
        if self._debug:
            payload_hex = " ".join(f"{b:02X}" for b in self._payload)
            self._log("debug", f"Payload:\n{payload_hex}")
        if self._msg_id == 0x83:  # 0x83 is successful ACK of setting binary nav type
            self.last_update_status = "Received ACK message, not nav data"
            return False
        if self._msg_id == 0x84:  # 0x84 is NACK
            self.last_update_status = "Received NACK message, not nav data"
            return False
        return True

    def _check_nav_data(self) -> bool:
        if self._msg_id != 0xDF:
            self.last_update_status = f"Invalid message ID, expected 0xDF, got: {hex(self._msg_id)}"
            return False
        return True

    def _parse_nav_data(self) -> bool:
        if self._payload_len != 81:
            self.last_update_status = f"Invalid payload length, expected 81, got: {self._payload_len}"
            return False
        return self._parse_data_AN0030()

    def _checksum(self) -> bool:  # Checksum is simply XOR sequentially of the payload ID + payload bytes
        cs = 0
        for i in self._payload:
            i = int(i)
            cs ^= i
        if cs != self._msg_cs:
            self.last_update_status = "Checksum failed!"
            return False
        return True

    def _parse_data_AN0030(self) -> bool:
        """
        Parse SkyTraq AN0030 Navigation Data Message (ID 0xDF) payload using the
        (typed helpers, no manual bit shifting).
        """
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
            self.unix_time = self._gps_time_2_unix_time(self.week, self.tow)
            if self._debug:
                self._log("debug", "Printing navigation data")
                self._print_nav_data()
            return True
        except Exception as e:
            self.last_update_status = f"Error parsing AN0030 data: {e}"
            self._log("error", f"Error parsing AN0030 data: {e}")
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
    Fix Modes in GPS Binary Message (S1216F8-GL):

    0 - No fix: The GPS receiver has not obtained a valid fix or has lost the fix.
    1 - Predicted fix: Still not valid, but the receiver is indicating a prediction
    2 - 2D fix: A 2D fix is available
    3 - 3D fix: A 3D fix is available
    4 - 3D + GNSS fix: A fix using signals from multiple GNSS systems
    """

    def has_fix(self) -> bool:
        """True if a current fix for location information is available."""
        if self.fix_mode is not None and self.fix_mode >= 2:
            return True
        else:
            return False

    def has_3d_fix(self) -> bool:
        """Returns true if there is a 3d fix available.
        use has_fix to determine if a 2d fix is available,
        passing it the same data"""
        if self.fix_mode is not None and self.fix_mode >= 3:
            return True
        else:
            return False

    def _is_leap_year(self, year):
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

    def _gps_time_2_unix_time(self, gps_week: int, tow: float) -> int:
        # Number of days in each month (non-leap year)
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

        total_gps_seconds = gps_week * 7 * 86400 + int(tow)
        total_utc_seconds = total_gps_seconds - _GPS_UTC_OFFSET_SECONDS
        total_days, seconds_in_day = divmod(total_utc_seconds, 86400)

        # Start from the epoch date and add total days
        year = EPOCH_YEAR
        month = EPOCH_MONTH
        day = EPOCH_DAY

        while total_days > 0:
            # Adjust days in February for leap years
            if self._is_leap_year(year):
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
        days_since_unix_epoch = (year - 1970) * 365 + sum(self._is_leap_year(y) for y in range(1970, year))
        for m in range(1, month):
            days_since_unix_epoch += days_in_month[m - 1]
        days_since_unix_epoch += day - 1

        # Convert days to seconds and add sub-day TOW seconds
        unix_time = days_since_unix_epoch * 86400 + seconds_in_day

        # Calculate hours, minutes, and seconds
        hours = seconds_in_day // 3600
        minutes = (seconds_in_day % 3600) // 60
        seconds = seconds_in_day % 60

        self.timestamp_utc = {
            "year": year,
            "month": month,
            "day": day,
            "hour": hours,
            "minute": minutes,
            "second": seconds,
        }

        # Return the unix time
        return unix_time

    def _print_nav_data(self) -> None:
        """Logs the current navigation data."""
        self.nav_data = self._get_nav_data()

        for key in self._ordered_keys:
            if key in self.nav_data:
                self._log("info", f"{key}: {self.nav_data[key]}")

    def _get_nav_data(self) -> dict:
        """Returns the current navigation data as a dictionary."""
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

    def _write(self, bytestr) -> Optional[int]:
        return self._uart.write(bytestr)

    def _send_binary(self, bytestr) -> None:
        self._write(bytestr)

    def _reset_to_factory_defaults(self) -> None:
        """Send Reset to Factory Defaults command (Message ID 0x04)."""
        self._write(b"\xa0\xa1\x00\x02\x04\x00\x04\x0d\x0a")

    def _set_to_binary(self) -> None:
        """Send Set to Binary Mode command (Message ID 0x09)."""
        # self._write(b"\xa0\xa1\x00\x03\x09\x02\x00\x0b\x0d\x0a")
        self._write(b"\xa0\xa1\x00\x03\x09\x02\x01\x0a\x0d\x0a")  # Flash memory version

    def _query_binary_status(self) -> None:
        """Send Query Binary Status command."""
        # (Message ID 0x1F)
        self._write(b"\xa0\xa1\x00\x01\x1F\x1F\x0d\x0a")

    def _enable_periodic_nav_data(self) -> None:
        """Send Enable Periodic Navigation Data command."""

        # (Message ID 0x11)
        # self._write(b"\xa0\xa1\x00\x09\x1e\x00\x00\x00\x00\x01\x03\x00\x00\x1c\x0d\x0a")
        self._write(b"\xa0\xa1\x00\x09\x1e\x00\x00\x00\x00\x01\x03\x00\x01\x1d\x0d\x0a")  # Flash memory version

    def _disable_nmea_periodic(self) -> None:
        """Send Disable NMEA Periodic Messages command (Message ID 0x64)."""
        self._write(b"\xa0\xa1\x00\x0F\x64\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x67\x0d\x0a")

    def _disable_unnecessary_binary_data(self) -> None:
        """Send Disable Unecessary Nav Binary Messages command (Message ID 0x1E)."""
        # self._write(b"\xa0\xa1\x00\x09\x1e\x00\x00\x00\x00\x01\x03\x00\x00\x1c\x0d\x0a")
        self._write(b"\xa0\xa1\x00\x09\x1e\x00\x00\x00\x00\x01\x03\x00\x01\x1d\x0d\x0a")  # Flash memory version

    def _use_helper_functions(self) -> None:
        """Use helper functions to set up the receiver hardware configuration."""
        if self._debug:
            self._log("debug", "Helper Functions: S1216F8-GL")

        # Helper Statements
        if self._RESET_TO_FACTORY:
            self._reset_to_factory_defaults()
            self._RESET_TO_FACTORY = False
            if self._debug:
                self._log("debug", "Resetting to factory defaults")
            return

        if self._DISABLE_NMEA_FLAG:
            self._disable_nmea_periodic()
            self._DISABLE_NMEA_FLAG = False
            if self._debug:
                self._log("debug", "Disabling NMEA")
            return

        if self._BINARY_SET_FLAG:
            self._set_to_binary()
            self._BINARY_SET_FLAG = False
            if self._debug:
                self._log("debug", "Setting receiver to binary mode")
            return

        if self._QUERIED_BINARY_STATUS_FLAG:
            self._query_binary_status()
            self._QUERIED_BINARY_STATUS_FLAG = False
            if self._debug:
                self._log("debug", "Querying binary status")
            return

        if self._PERIODIC_NAV_FLAG:
            self._enable_periodic_nav_data()
            self._PERIODIC_NAV_FLAG = False
            if self._debug:
                self._log("debug", "Enabling periodic navigation data")
            return

        if self._DISABLE_UNNECESSARY_BINARY_FLAG:
            self._disable_unnecessary_binary_data()
            self._DISABLE_UNNECESSARY_BINARY_FLAG = False
            if self._debug:
                self._log("debug", "Disabling unnecessary binary data")
            return

    @property
    def _in_waiting(self) -> int:
        return self._uart.in_waiting

    def readline(self) -> Optional[bytes]:
        return self._uart.readline()

    def read(self, nbytes: int) -> Optional[bytes]:
        return self._uart.read(nbytes)

    def _discard_rx_prefix(self, count: int) -> None:
        if count <= 0:
            return
        self._rx_buffer = bytearray(self._rx_buffer[count:])

    def _keep_rx_suffix(self, count: int) -> None:
        if count <= 0:
            self._rx_buffer = bytearray()
            return
        self._rx_buffer = bytearray(self._rx_buffer[-count:])

    def _log_rx_buffer_size(self) -> None:
        buffer_len = len(self._rx_buffer)
        if self._debug:
            self._log("debug", f"RX buffer size: {buffer_len}/{self._max_rx_buffer_len}")

        warn_threshold = self._max_rx_buffer_len - max(1, self._max_rx_buffer_len // _RX_BUFFER_WARN_FRACTION)
        if buffer_len >= warn_threshold:
            self._log("warning", f"RX buffer nearing limit: {buffer_len}/{self._max_rx_buffer_len}")

    def _read_available_bytes(self) -> None:
        while self._in_waiting > 0:
            chunk = self.read(self._in_waiting)
            if not chunk:
                return
            self._rx_buffer.extend(chunk)
            self._log_rx_buffer_size()

        if len(self._rx_buffer) > self._max_rx_buffer_len:
            self._log("warning", f"RX buffer exceeded limit, trimming to {self._max_rx_buffer_len} bytes")
            self._keep_rx_suffix(self._max_rx_buffer_len)
            self._log_rx_buffer_size()

    def _extract_frame(self) -> Optional[bytes]:
        while len(self._rx_buffer) >= 2:
            start_idx = self._rx_buffer.find(_FRAME_START)
            if start_idx < 0:
                if len(self._rx_buffer) > 1:
                    self._keep_rx_suffix(1)
                return None

            if start_idx > 0:
                self._discard_rx_prefix(start_idx)

            if len(self._rx_buffer) < 4:
                return None

            payload_len = (self._rx_buffer[2] << 8) | self._rx_buffer[3]
            if payload_len == 0 or payload_len > _MAX_FRAME_PAYLOAD_LEN:
                self._discard_rx_prefix(1)
                continue

            frame_len = payload_len + 7
            if len(self._rx_buffer) < frame_len:
                return None

            if bytes(self._rx_buffer[frame_len - 2 : frame_len]) != _FRAME_END:
                self._discard_rx_prefix(1)
                continue

            frame = bytes(self._rx_buffer[:frame_len])
            self._discard_rx_prefix(frame_len)
            return frame

        return None

    def read_sentence(self) -> Optional[bytes]:
        self._read_available_bytes()

        if len(self._rx_buffer) < _MIN_FRAME_LEN:
            return None

        latest_frame = None
        latest_nav_frame = None

        while True:
            frame = self._extract_frame()
            if frame is None:
                break

            latest_frame = frame
            if len(frame) >= 5 and frame[4] == 0xDF:
                latest_nav_frame = frame

        return latest_nav_frame or latest_frame

    ######################## ERROR HANDLING ########################

    @property
    def device_errors(self):
        return []

    def deinit(self):
        if self._enable is not None:
            self._enable.deinit()
            self._enable = None
        return
