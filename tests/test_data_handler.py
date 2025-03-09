# isort: skip_file
import os

import pytest

import tests.cp_mock  # noqa: F401
import flight.core.data_handler as dh
from flight.core.data_handler import DataProcess as DP
from flight.core.data_handler import extract_time_from_filename, get_closest_file_time


@pytest.mark.parametrize(
    "data_format, expected_size",
    [
        (
            "<bBhHiIlLqQfd",
            1 + 1 + 2 + 2 + 4 + 4 + 4 + 4 + 8 + 8 + 4 + 8,
        ),  # example with all format characters
        ("<iIf", 4 + 4 + 4),  # int, unsigned int and float
        ("<hH", 2 + 2),  # short and unsigned short
        ("<Qd", 8 + 8),  # unsigned long long and double
        ("<bB", 1 + 1),  # byte and unsigned byte
    ],
)
def test_compute_bytesize(data_format, expected_size):
    assert DP.compute_bytesize(data_format) == expected_size


# Testing invalid format characters
@pytest.mark.parametrize(
    "invalid_format",
    [
        "<Ifz",  # invalid format character 'z'
        "<abc",  # multiple invalid format characters 'a', 'b', 'c'
    ],
)
def test_compute_bytesize_invalid_format(invalid_format):
    with pytest.raises(ValueError):
        DP.compute_bytesize(invalid_format)


@pytest.mark.parametrize(
    "input_paths, expected_output",
    [
        (("a", "b", "c"), "a/b/c"),
        (("a", "/b", "c"), "a/b/c"),
        (("", "b", "c"), "b/c"),
        ((".", "b", "c"), os.path.join(".", "b", "c")),
        (("a", ".", "c"), os.path.join("a", ".", "c")),
        (("a",), os.path.join("a")),
        ((), ""),
    ],
)
def test_join_path(input_paths, expected_output):
    assert dh.join_path(*input_paths) == expected_output


@pytest.mark.parametrize(
    "input_filename, expected_output",
    [
        ("imu_1700001234.bin", 1700001234),
        ("img_1699999999.bin", 1699999999),
        ("gps_.bin", None),
        ("not_correct_format", None),
    ],
)
def test_extract_time_from_filename(input_filename, expected_output):
    assert extract_time_from_filename(input_filename) == expected_output


@pytest.mark.parametrize(
    "file_time, expected_output",
    [
        (1700001234, "imu_1700001234.bin"),  # Exact time
        (1739719846, "cdh_1739719847.bin"),
        (1739720168, "thermal_1739720103.bin"),
        (1699900000, "img_1699999999.bin"),
        (1589387500, "comms_1589387566.bin"),
    ],
)
def test_get_closest_file_time(file_time, expected_output):
    files = [
        "imu_1700001234.bin",
        "cdh_1739719847.bin",
        "thermal_1739720103.bin",
        "img_1699999999.bin",
        "comms_1589387566.bin",
    ]
    assert get_closest_file_time(file_time, files) == expected_output

    invalid_files = [
        "imu.bin",
        "cdh.bin",
        "thermal.bin",
        "img.bin",
        "comms.bin",
    ]

    assert get_closest_file_time(file_time, invalid_files) is None


# TODO - mock filesystem

"""@pytest.fixture
def sd_root(tmpdir):
    sd_root = tmpdir.mkdir("sd")
    return sd_root

def test_scan_sd_card(sd_root):
    DH.sd_path = str(sd_root)"""

if __name__ == "__main__":
    pytest.main()
