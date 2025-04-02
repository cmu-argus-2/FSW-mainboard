# isort: skip_file
import os

import pytest

import tests.cp_mock  # noqa: F401
import flight.core.data_handler as dh
from flight.core.data_handler import DataProcess as DP
from flight.core.data_handler import extract_time_from_filename, get_closest_file_time
from time import perf_counter

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


@pytest.fixture
def sd_root(tmp_path):
    """
    Creates a temporary SD card root directory for testing.
    Ensures the path exists before tests use it.
    """
    sd_root = tmp_path / "sd_root"
    sd_root.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
    return sd_root


def test_image_nominal_log(sd_root):
    dh._HOME_PATH = str(sd_root)  # temporary SD card
    DH.register_image_process()
    assert dh._IMG_TAG_NAME in DH.data_process_registry  # ensure that image process was registered

    DH.log_image(bytearray(100))  # Adding 100 bytes
    img_process = DH.data_process_registry[dh._IMG_TAG_NAME]
    assert img_process.img_buf_index == 100

    DH.log_image(bytearray(412))  # Adding remaining 412 bytes
    assert os.stat(img_process.current_path).st_size == 512  # Ensure block of 512 was written to file

    DH.log_image(bytearray(700))  # Testing overflow
    assert img_process.img_buf_index == 188
    assert os.stat(img_process.current_path).st_size == 1024

    DH.log_image(bytearray(200))  # Testing not writing if not 512 block
    assert img_process.img_buf_index == 388
    assert os.stat(img_process.current_path).st_size == 1024

    DH.log_image(bytearray(200))  # Testing a second 512 write
    assert img_process.img_buf_index == 76
    assert os.stat(img_process.current_path).st_size == 1536


def test_image_edge_case_log(sd_root):
    # Testing Edge cases with image buffer
    dh._HOME_PATH = str(sd_root)  # temporary SD card
    DH.register_image_process()
    assert dh._IMG_TAG_NAME in DH.data_process_registry  # ensure that image process was registered
    img_process = DH.data_process_registry[dh._IMG_TAG_NAME]

    # Writing exactly 512 bytes at once
    DH.log_image(bytearray(512))
    assert os.stat(img_process.current_path).st_size == 512
    assert img_process.img_buf_index == 0  # Buffer resets after write

    # Writing nothing should not affect buffer
    DH.log_image(bytearray(0))
    assert img_process.img_buf_index == 0  # Should still be empty
    assert os.stat(img_process.current_path).st_size == 512  # No additional writes

    # Overflow handling when adding 1024 bytes
    DH.log_image(bytearray(1024))
    assert os.stat(img_process.current_path).st_size == 1536  # Two full writes
    assert img_process.img_buf_index == 0  # Buffer should be empty after exact writes

    # Writing in small increments without reaching 512
    DH.log_image(bytearray(100))
    assert img_process.img_buf_index == 100
    assert os.stat(img_process.current_path).st_size == 1536  # No new writes

    DH.log_image(bytearray(411))
    assert img_process.img_buf_index == 511  # Still no write yet
    assert os.stat(img_process.current_path).st_size == 1536

    DH.log_image(bytearray(1))  # This should push buffer to 512, triggering a write
    assert img_process.img_buf_index == 0  # Buffer resets
    assert os.stat(img_process.current_path).st_size == 2048  # New block written


def test_computing_total_size_files(sd_root):
    sub_system = ["img", "cdh", "cmd_logs", "adcs", "eps", "comms"]
    file_mock_time = [1700001234, 1739719846, 1739720168, 1699900000, 1589387500]
    # Fill sd_root with test files
    for i in range(len(sub_system)):
        subdir = sd_root / f"{sub_system[i]}"
        subdir.mkdir()
        for j in range(5):
            (subdir / f"{sub_system[i]}_{file_mock_time[j]}.bin").write_bytes(b"1234567890" * 100)  # ~1KB

    dh._HOME_PATH = str(sd_root)  # temporary SD card
    time_start = perf_counter()
    total_size = DH.compute_total_size_files(str(sd_root))
    time_end = perf_counter()

    # Sanity check: 6 subsystems * 5 files * 1000 bytes = 30,000 bytes
    assert total_size == 6 * 5 * 1000

    print(f"Time: {time_end - time_start}, Size: {total_size}")

    DH.delete_all_files(str(sd_root))
    time_start = perf_counter()
    total_size = DH.compute_total_size_files(str(sd_root))
    time_end = perf_counter()

    print(f"Time: {time_end - time_start}, Size: {total_size}")

    assert total_size == 0


if __name__ == "__main__":
    pytest.main()
