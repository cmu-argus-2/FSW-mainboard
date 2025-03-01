# isort: skip_file
import os

import pytest

import tests.cp_mock  # noqa: F401
import flight.core.data_handler as dh
from flight.core.data_handler import DataProcess as DP
from flight.core.data_handler import extract_time_from_filename

DH = dh.DataHandler


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


# TODO - mock filesystem


@pytest.fixture
def sd_root(tmpdir):
    sd_root = tmpdir.mkdir(dh._HOME_PATH)
    return sd_root


def test_image_log(sd_root):
    dh._HOME_PATH = str(sd_root)  # temporary SD card
    DH.register_image_process()
    assert dh._IMG_TAG_NAME in DH.data_process_registry  # ensure that image process was registered

    DH.log_image(bytearray(100))  # Adding 100 bytes
    img_process = DH.data_process_registry[dh._IMG_TAG_NAME]
    assert img_process.img_buf_index == 100

    DH.log_image(bytearray(412))  # Adding remaining 412 bytes
    assert os.stat(img_process.current_path)[6] == 512  # Ensure block of 512 was written to file

    DH.log_image(bytearray(700))  # Testing overflow
    assert img_process.img_buf_index == 188
    assert os.stat(img_process.current_path)[6] == 1024

    DH.log_image(bytearray(200))  # Testing not writing if not 512 block
    assert img_process.img_buf_index == 388
    assert os.stat(img_process.current_path)[6] == 1024

    DH.log_image(bytearray(200))  # Testing a second 512 write
    assert img_process.img_buf_index == 76
    assert os.stat(img_process.current_path)[6] == 1536


if __name__ == "__main__":
    pytest.main()
