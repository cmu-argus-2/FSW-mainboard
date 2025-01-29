import unittest
from unittest.mock import MagicMock
from gps import GPS

class MockUART:
    def __init__(self, response=None):
        self.response = response or b''
        self.in_waiting = len(self.response)

    def readline(self):
        return self.response

    def write(self, bytestr):
        return len(bytestr)

class TestGPS(unittest.TestCase):
    def setUp(self):
        self.mock_uart = MockUART()
        self.gps = GPS(uart=self.mock_uart, mock=True)

    def test_initialization(self):
        self.assertIsInstance(self.gps, GPS)
        self.assertTrue(self.gps.mock)
        self.assertIsNotNone(self.gps._nav_data_hex)

    def test_update_with_mock_data(self):
        self.mock_uart.response = self.gps.mock_message
        self.mock_uart.in_waiting = len(self.mock_uart.response)

        updated = self.gps.update()
        self.assertTrue(updated)
        self.assertEqual(self.gps._msg_id, 0xA8)
        self.assertEqual(self.gps._payload_len, 59)

    def test_parse_fix_mode(self):
        self.gps._nav_data_hex["fix_mode"] = 2  # 3D fix
        fix_mode = self.gps.parse_fix_mode()
        self.assertEqual(fix_mode, 2)

    def test_has_fix(self):
        self.gps._nav_data_hex["fix_mode"] = 1
        self.assertTrue(self.gps.has_fix())

    def test_has_3d_fix(self):
        self.gps._nav_data_hex["fix_mode"] = 2
        self.assertTrue(self.gps.has_3d_fix())

    def test_parse_latitude(self):
        self.gps._nav_data_hex["latitude"] = 374221234  # example value
        lat = self.gps.parse_lat()
        self.assertEqual(lat, 374221234)

    def test_parse_longitude(self):
        self.gps._nav_data_hex["longitude"] = -1220845678  # example value
        lon = self.gps.parse_lon()
        self.assertEqual(lon, -1220845678)

    def test_print_parsed_strings(self):
        self.gps.update()
        self.gps.print_parsed_strings()

if __name__ == "__main__":
    unittest.main()