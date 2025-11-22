# isort: skip_file
import os

import pytest

import tests.cp_mock  # noqa: F401
import flight.core.data_handler as dh
from flight.core.data_handler import DataProcess as DP
from flight.core.data_handler import extract_time_from_filename, get_closest_file_time

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


def test_file_process_nominal_log(sd_root):
    """Test nominal file process logging with fixed-size packets."""
    dh._HOME_PATH = str(sd_root)  # temporary SD card
    file_tag = "test_file"
    DH.register_file_process(tag_name=file_tag, buffer_size=512)
    assert file_tag in DH.data_process_registry  # ensure that file process was registered

    file_process = DH.data_process_registry[file_tag]

    # Log a packet smaller than max size (242 - 2 = 240 bytes max payload)
    data1 = bytearray(100)
    DH.log_file(file_tag, data1)

    # Each packet is fixed at 242 bytes (dh._FIXED_PACKET_SIZE)
    # Buffer index should be at 242
    assert file_process.file_buf_index == dh._FIXED_PACKET_SIZE
    assert file_process.packet_count == 1

    # Log second packet (another 242 bytes fixed)
    data2 = bytearray(150)
    DH.log_file(file_tag, data2)
    assert file_process.file_buf_index == dh._FIXED_PACKET_SIZE * 2
    assert file_process.packet_count == 2

    # Log third packet (242 bytes), triggering write when buffer reaches 512
    data3 = bytearray(120)
    DH.log_file(file_tag, data3)
    # After 3 packets (726 bytes), buffer should have written 512 bytes and kept the rest
    assert os.stat(file_process.current_path).st_size == 512 + dh._DH_FILE_HEADER_SIZE  # One block written
    assert file_process.file_buf_index == 214  # Remaining 214 bytes in buffer (726 - 512)
    assert file_process.packet_count == 3


def test_file_process_packet_retrieval(sd_root):
    """Test packet retrieval with fixed-size packets (O(1) access)."""
    dh._HOME_PATH = str(sd_root)  # temporary SD card
    file_tag = "test_retrieval"
    DH.register_file_process(tag_name=file_tag, buffer_size=512)

    file_process = DH.data_process_registry[file_tag]

    # Log multiple packets with different data
    test_data = [
        bytearray([1, 2, 3, 4, 5]),
        bytearray([10, 20, 30, 40]),
        bytearray([100, 200] * 50),  # 100 bytes
    ]

    for data in test_data:
        DH.log_file(file_tag, data)

    # Force flush buffer to disk
    DH.file_completed(file_tag)

    filepath = file_process.current_path

    # Test O(1) packet count
    packet_count = file_process.get_packet_count(filepath)
    assert packet_count == 3, f"Expected 3 packets, got {packet_count}"

    # Test O(1) direct packet access
    result0 = file_process.get_packet(filepath, 0)
    assert result0 is not None, "Packet 0 should exist"
    length0, data0 = result0
    assert length0 == len(test_data[0]), "Packet 0 length mismatch"
    assert data0 == test_data[0], "Packet 0 data mismatch"

    result1 = file_process.get_packet(filepath, 1)
    assert result1 is not None, "Packet 1 should exist"
    length1, data1 = result1
    assert length1 == len(test_data[1]), "Packet 1 length mismatch"
    assert data1 == test_data[1], "Packet 1 data mismatch"

    result2 = file_process.get_packet(filepath, 2)
    assert result2 is not None, "Packet 2 should exist"
    length2, data2 = result2
    assert length2 == len(test_data[2]), "Packet 2 length mismatch"
    assert data2 == test_data[2], "Packet 2 data mismatch"

    # Test out of bounds access
    packet_none = file_process.get_packet(filepath, 10)
    assert packet_none is None, "Should return None for out of bounds index"


def test_file_process_fixed_packet_structure(sd_root):
    """Test that packets are stored with fixed size and proper padding."""
    dh._HOME_PATH = str(sd_root)  # temporary SD card
    file_tag = "test_structure"
    DH.register_file_process(tag_name=file_tag, buffer_size=512)

    file_process = DH.data_process_registry[file_tag]

    # Log a small packet
    small_data = bytearray([1, 2, 3])
    DH.log_file(file_tag, small_data)

    # Force flush to disk
    DH.file_completed(file_tag)

    filepath = file_process.current_path

    # Verify file size is exactly one fixed packet size (200 bytes)
    file_size = os.stat(filepath).st_size
    assert (
        file_size == dh._FIXED_PACKET_SIZE + dh._DH_FILE_HEADER_SIZE
    ), f"Expected {dh._FIXED_PACKET_SIZE + dh._DH_FILE_HEADER_SIZE} bytes, got {file_size}"

    # Read raw bytes and verify structure
    with open(filepath, "rb") as f:
        raw_packet = f.read()

    # Verify file header
    file_header = raw_packet[0 : dh._DH_FILE_HEADER_SIZE]
    assert file_header == dh._DH_MAGIC_NUMBER, "File header magic mismatch"

    # First 2 bytes should be the length (3 in big-endian)
    length = int.from_bytes(raw_packet[dh._DH_FILE_HEADER_SIZE : dh._DH_FILE_HEADER_SIZE + dh._PACKET_HEADER_SIZE], "big")
    assert length == 3, f"Expected length 3, got {length}"

    # Next 3 bytes should be the actual data
    actual_data = raw_packet[
        dh._DH_FILE_HEADER_SIZE + dh._PACKET_HEADER_SIZE : dh._DH_FILE_HEADER_SIZE + dh._PACKET_HEADER_SIZE + length
    ]
    assert actual_data == bytes([1, 2, 3]), "Data mismatch"

    # Remaining bytes should be padding (zeros)
    padding = raw_packet[dh._DH_FILE_HEADER_SIZE + dh._PACKET_HEADER_SIZE + length :]
    assert len(padding) == dh._FIXED_PACKET_SIZE - dh._PACKET_HEADER_SIZE - length, "Padding length mismatch"
    assert all(b == 0 for b in padding), "Padding should be all zeros"


def test_file_process_max_data_size(sd_root):
    """Test handling of maximum data size per packet."""
    dh._HOME_PATH = str(sd_root)  # temporary SD card
    file_tag = "test_max_size"
    DH.register_file_process(tag_name=file_tag, buffer_size=512)

    file_process = DH.data_process_registry[file_tag]

    # Maximum data size is FIXED_PACKET_SIZE - HEADER_SIZE = 200 - 2 = 198 bytes
    max_data_size = dh._FIXED_PACKET_SIZE - dh._PACKET_HEADER_SIZE

    # Log packet at exactly max size
    max_data = bytearray(range(max_data_size))
    DH.log_file(file_tag, max_data)
    assert file_process.packet_count == 1

    # Log packet exceeding max size (should fail/log error)
    oversized_data = bytearray(max_data_size + 1)
    initial_count = file_process.packet_count
    DH.log_file(file_tag, oversized_data)
    # Packet count should not increase for oversized data
    assert file_process.packet_count == initial_count, "Oversized packet should not be logged"

    # Flush and verify retrieval
    DH.file_completed(file_tag)
    filepath = file_process.current_path

    result = file_process.get_packet(filepath, 0)
    assert result is not None, "Max size packet should exist"
    retrieved_length, retrieved_data = result
    assert retrieved_length == max_data_size, f"Expected length {max_data_size}, got {retrieved_length}"
    assert retrieved_data == max_data, "Max size packet retrieval failed"


def test_file_process_image_reconstruction(sd_root, tmp_path):
    """Test reading a real image, storing as packets, and reconstructing it."""
    dh._HOME_PATH = str(sd_root)  # temporary SD card
    file_tag = "test_image"
    DH.register_file_process(tag_name=file_tag, buffer_size=512)

    file_process = DH.data_process_registry[file_tag]

    # Read the test image
    test_image_path = os.path.join(os.path.dirname(__file__), "test_image.jpg")
    with open(test_image_path, "rb") as f:
        original_image_data = f.read()

    original_size = len(original_image_data)

    # Calculate max data per packet
    max_data_size = dh._FIXED_PACKET_SIZE - dh._PACKET_HEADER_SIZE  # 198 bytes

    # Split image into packets and log them
    offset = 0
    packet_count = 0
    while offset < original_size:
        chunk_size = min(max_data_size, original_size - offset)
        chunk = bytearray(original_image_data[offset : offset + chunk_size])
        DH.log_file(file_tag, chunk)
        offset += chunk_size
        packet_count += 1

    # Complete the file (flush buffer)
    DH.file_completed(file_tag)

    filepath = file_process.current_path

    # Verify packet count
    stored_packet_count = file_process.get_packet_count(filepath)
    assert stored_packet_count == packet_count, f"Expected {packet_count} packets, got {stored_packet_count}"

    # Reconstruct the image by reading all packets
    reconstructed_data = bytearray()
    for i in range(packet_count):
        result = file_process.get_packet(filepath, i)
        assert result is not None, f"Packet {i} should exist"
        length, data = result
        reconstructed_data.extend(data)

    # Verify reconstructed data matches original
    assert len(reconstructed_data) == original_size, f"Size mismatch: {len(reconstructed_data)} vs {original_size}"
    assert reconstructed_data == bytearray(original_image_data), "Reconstructed data does not match original"

    # Write reconstructed image to verify it's valid
    output_path = tmp_path / "reconstructed_image.jpg"
    with open(output_path, "wb") as f:
        f.write(reconstructed_data)

    # Verify the output file exists and has correct size
    assert os.path.exists(output_path), "Reconstructed image file was not created"
    output_size = os.path.getsize(output_path)
    assert output_size == original_size, f"Output size mismatch: {output_size} vs {original_size}"


def test_file_process_custom_packet_reconstruction(sd_root, tmp_path):
    """Test reading a binary file with custom packet headers, storing, and reconstructing it."""
    import struct
    from dataclasses import dataclass

    @dataclass
    class PacketHeader:
        payload_size_bytes: int  # u16: actual payload size in this fragment
        page_id: int  # u16: image/page ID
        tile_idx: int  # u16: tile index
        frag_idx: int  # u8: fragment index within tile

        def to_bytes(self) -> bytes:
            # >HHHB = big-endian: u16, u16, u16, u8
            return struct.pack(">HHHB", self.payload_size_bytes, self.page_id, self.tile_idx, self.frag_idx)

        @staticmethod
        def from_bytes(data: bytes) -> "PacketHeader":
            payload_size, page_id, tile_idx, frag_idx = struct.unpack(">HHHB", data)
            return PacketHeader(payload_size, page_id, tile_idx, frag_idx)

        @staticmethod
        def size_bytes() -> int:
            return 7

    dh._HOME_PATH = str(sd_root)  # temporary SD card
    file_tag = "test_custom_binary"
    DH.register_file_process(tag_name=file_tag, buffer_size=512)

    file_process = DH.data_process_registry[file_tag]

    # Read the test binary file with custom packet structure
    test_bin_path = os.path.join(os.path.dirname(__file__), "test_image.bin")
    with open(test_bin_path, "rb") as f:
        original_bin_data = f.read()

    original_size = len(original_bin_data)

    # Calculate max data per packet for FileProcess
    max_data_size = dh._FIXED_PACKET_SIZE - dh._PACKET_HEADER_SIZE  # 238 bytes with 240 byte packets

    # Parse the original binary file to extract custom packets
    original_packets = []
    offset = 0
    header_size = PacketHeader.size_bytes()

    while offset < original_size:
        if offset + header_size > original_size:
            break  # Not enough data for a header

        # Read custom packet header
        header_bytes = original_bin_data[offset : offset + header_size]
        header = PacketHeader.from_bytes(header_bytes)

        # Read payload
        payload_start = offset + header_size
        payload_end = payload_start + header.payload_size_bytes

        if payload_end > original_size:
            break  # Not enough data for payload

        payload = original_bin_data[payload_start:payload_end]

        # Store the complete custom packet (header + payload) together
        complete_packet = header_bytes + payload
        original_packets.append(complete_packet)

        offset = payload_end

    # Store each custom packet (header + payload) as a single FileProcess packet
    for i, packet_data in enumerate(original_packets):
        # Check if this packet fits in one FileProcess packet
        if len(packet_data) <= max_data_size:
            # Fits in one packet - store as is
            DH.log_file(file_tag, bytearray(packet_data))
        else:
            # Need to split across multiple FileProcess packets
            pkt_offset = 0
            while pkt_offset < len(packet_data):
                chunk_size = min(max_data_size, len(packet_data) - pkt_offset)
                chunk = bytearray(packet_data[pkt_offset : pkt_offset + chunk_size])
                DH.log_file(file_tag, chunk)
                pkt_offset += chunk_size

    # Complete the file (flush buffer)
    DH.file_completed(file_tag)

    filepath = file_process.current_path
    stored_packet_count = file_process.get_packet_count(filepath)

    # Reconstruct the binary file by reading all FileProcess packets
    reconstructed_data = bytearray()
    for i in range(stored_packet_count):
        result = file_process.get_packet(filepath, i)
        assert result is not None, f"Packet {i} should exist"
        length, data = result
        reconstructed_data.extend(data)

    # Verify reconstructed data matches original
    assert len(reconstructed_data) == original_size, f"Size mismatch: {len(reconstructed_data)} vs {original_size}"
    assert reconstructed_data == bytearray(original_bin_data), "Reconstructed data does not match original"

    # Write reconstructed binary file
    output_path = tmp_path / "reconstructed_image.bin"
    with open(output_path, "wb") as f:
        f.write(reconstructed_data)

    # Verify the output file exists and has correct size
    assert os.path.exists(output_path), "Reconstructed binary file was not created"
    output_size = os.path.getsize(output_path)
    assert output_size == original_size, f"Output size mismatch: {output_size} vs {original_size}"

    # Verify we can parse the reconstructed file and get the same packets
    reconstructed_packets = []
    offset = 0
    while offset < len(reconstructed_data):
        if offset + header_size > len(reconstructed_data):
            break

        header_bytes = reconstructed_data[offset : offset + header_size]
        header = PacketHeader.from_bytes(header_bytes)

        payload_start = offset + header_size
        payload_end = payload_start + header.payload_size_bytes

        if payload_end > len(reconstructed_data):
            break

        payload = reconstructed_data[payload_start:payload_end]
        complete_packet = header_bytes + payload
        reconstructed_packets.append(complete_packet)

        offset = payload_end

    assert len(reconstructed_packets) == len(original_packets), "Packet count mismatch after reconstruction"

    # Verify each packet matches
    for i, (orig, recon) in enumerate(zip(original_packets, reconstructed_packets)):
        assert orig == recon, f"Packet {i} mismatch"


if __name__ == "__main__":
    pytest.main()
