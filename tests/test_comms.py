# isort: skip_file
import os
import sys
import struct
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest

import tests.cp_mock  # noqa: F401
import core.data_handler as dh
from apps.comms.comms import MSG_ID, SATELLITE_RADIO
from core.data_handler import DataHandler as DH

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
flight_dir = os.path.join(project_root, "flight")
if flight_dir not in sys.path:
    sys.path.insert(0, flight_dir)


# Mock SATELLITE for actual hardware interaction
@pytest.fixture
def satellite_radio():
    with patch("hal.configuration.SATELLITE") as mock_satellite:
        # Create mock RADIO with necessary attributes
        mock_satellite.RADIO_AVAILABLE = True
        mock_satellite.RADIO.RX_available = MagicMock(return_value=True)
        mock_satellite.RADIO.send = MagicMock()
        mock_satellite.RADIO.recv = MagicMock(return_value=(None, 0))

        yield SATELLITE_RADIO


@pytest.fixture
def sd_root(tmp_path):
    """
    Creates a temporary SD card root directory for testing with proper structure.
    Structure: sd_root/data/tag_name/files
    """
    sd_root = tmp_path / "sd"
    data_dir = sd_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return sd_root


@dataclass
class PacketHeader:
    """Custom packet header structure for binary file testing."""

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


def test_comms_file_metadata_transmission(sd_root):
    """Test that comms correctly transmits file metadata."""
    dh._HOME_PATH = str(sd_root)
    file_tag = "imu"

    DH.register_file_process(tag_name=file_tag, buffer_size=512)
    file_process = DH.data_process_registry[file_tag]

    test_data1 = bytearray([0xAA] * 150)
    test_data2 = bytearray([0xBB] * 100)
    DH.log_file(file_tag, test_data1)
    DH.log_file(file_tag, test_data2)
    DH.file_completed(file_tag)

    filepath = file_process.current_path

    SATELLITE_RADIO.filepath = filepath

    SATELLITE_RADIO.transmit_file_metadata()

    tx_message = SATELLITE_RADIO.tx_message

    assert tx_message[0] == MSG_ID.SAT_FILE_METADATA
    assert tx_message[3] == 0x0B

    file_id = tx_message[4]
    file_size = int.from_bytes(tx_message[9:13], "big")
    file_message_count = int.from_bytes(tx_message[13:15], "big")

    assert file_message_count == 2, f"Expected 2 packets, got {file_message_count}"
    assert file_size > 0, "File size should be greater than 0"
    assert file_id == 6, f"Expected IMU file_id=6, got {file_id}"


def test_comms_file_packet_transmission(sd_root):
    """Test individual packet transmission for file downlink."""
    dh._HOME_PATH = str(sd_root)
    file_tag = "cdh"

    DH.register_file_process(tag_name=file_tag, buffer_size=512)
    file_process = DH.data_process_registry[file_tag]

    test_packets = [
        bytearray([0xAA] * 100),
        bytearray([0xBB] * 150),
        bytearray([0xCC] * 200),
    ]

    for packet_data in test_packets:
        DH.log_file(file_tag, packet_data)
    DH.file_completed(file_tag)

    filepath = file_process.current_path

    SATELLITE_RADIO.filepath = filepath
    SATELLITE_RADIO.file_get_metadata()

    for idx in range(3):
        SATELLITE_RADIO.rq_sq_cnt = idx
        SATELLITE_RADIO.transmit_file_packet()

        tx_message = SATELLITE_RADIO.tx_message

        assert tx_message[0] == MSG_ID.SAT_FILE_PKT
        sq_cnt = int.from_bytes(tx_message[1:3], "big")
        assert sq_cnt == idx, f"Expected sq_cnt {idx}, got {sq_cnt}"

        payload_start = 4 + 1 + 4  # header(4) + file_id(1) + file_time(4)
        payload = tx_message[payload_start:]

        expected_byte = [0xAA, 0xBB, 0xCC][idx]
        expected_length = [100, 150, 200][idx]
        assert len(payload) == expected_length, f"Expected {expected_length} bytes, got {len(payload)}"
        assert all(b == expected_byte for b in payload), f"Packet {idx} data mismatch"


def test_comms_downlink_all_transmission(sd_root, satellite_radio):
    """Test bulk file download (DOWNLINK_ALL) transmission."""
    dh._HOME_PATH = str(sd_root)
    file_tag = "comms"

    DH.register_file_process(tag_name=file_tag, buffer_size=512)
    file_process = DH.data_process_registry[file_tag]

    test_packets = [bytearray([i] * 50) for i in range(5)]

    for packet_data in test_packets:
        DH.log_file(file_tag, packet_data)
    DH.file_completed(file_tag)

    filepath = file_process.current_path

    SATELLITE_RADIO.filepath = filepath
    SATELLITE_RADIO.handle_downlink_all_rq()

    assert SATELLITE_RADIO.dlink_all is True
    assert SATELLITE_RADIO.dlink_init is True
    assert SATELLITE_RADIO.int_sq_cnt == 0
    assert SATELLITE_RADIO.file_message_count == 5

    transmitted_packets = []
    for _ in range(5):
        SATELLITE_RADIO.transmit_downlink_all()
        tx_message = SATELLITE_RADIO.tx_message

        assert tx_message[0] == MSG_ID.SAT_DOWNLINK_ALL

        sq_cnt = int.from_bytes(tx_message[1:3], "big")
        payload_start = 4 + 1 + 4
        payload = tx_message[payload_start:]

        transmitted_packets.append((sq_cnt, bytes(payload)))

    assert len(transmitted_packets) == 5
    for idx, (sq_cnt, payload) in enumerate(transmitted_packets):
        assert sq_cnt == idx, f"Expected sq_cnt {idx}, got {sq_cnt}"
        expected_byte = idx
        assert len(payload) == 50, f"Expected 50 bytes, got {len(payload)}"
        assert all(b == expected_byte for b in payload), f"Packet {idx} data mismatch"

    assert SATELLITE_RADIO.dlink_all is False
    assert SATELLITE_RADIO.dlink_init is False


def test_comms_binary_file_reconstruction(sd_root, tmp_path):
    """
    Test complete binary file reconstruction using the custom packet format
    from the data handler tests. This verifies end-to-end file transmission.
    """
    dh._HOME_PATH = str(sd_root)
    file_tag = "img"

    DH.register_file_process(tag_name=file_tag, buffer_size=512)
    file_process = DH.data_process_registry[file_tag]

    test_bin_path = os.path.join(os.path.dirname(__file__), "test_image.bin")
    with open(test_bin_path, "rb") as f:
        original_bin_data = f.read()

    original_size = len(original_bin_data)
    max_data_size = dh._FIXED_PACKET_SIZE - dh._PACKET_HEADER_SIZE

    original_packets = []
    offset = 0
    header_size = PacketHeader.size_bytes()

    while offset < original_size:
        if offset + header_size > original_size:
            break

        header_bytes = original_bin_data[offset : offset + header_size]
        header = PacketHeader.from_bytes(header_bytes)

        payload_start = offset + header_size
        payload_end = payload_start + header.payload_size_bytes

        if payload_end > original_size:
            break

        payload = original_bin_data[payload_start:payload_end]
        complete_packet = header_bytes + payload
        original_packets.append(complete_packet)
        offset = payload_end

    for packet_data in original_packets:
        if len(packet_data) <= max_data_size:
            DH.log_file(file_tag, bytearray(packet_data))
        else:
            pkt_offset = 0
            while pkt_offset < len(packet_data):
                chunk_size = min(max_data_size, len(packet_data) - pkt_offset)
                chunk = bytearray(packet_data[pkt_offset : pkt_offset + chunk_size])
                DH.log_file(file_tag, chunk)
                pkt_offset += chunk_size

    DH.file_completed(file_tag)
    filepath = file_process.current_path

    SATELLITE_RADIO.filepath = filepath
    SATELLITE_RADIO.file_get_metadata()

    packet_count = SATELLITE_RADIO.file_message_count

    reconstructed_data = bytearray()
    for idx in range(packet_count):
        SATELLITE_RADIO.rq_sq_cnt = idx
        SATELLITE_RADIO.transmit_file_packet()

        tx_message = SATELLITE_RADIO.tx_message

        payload_start = 4 + 1 + 4
        payload = tx_message[payload_start:]
        reconstructed_data.extend(payload)

    assert len(reconstructed_data) == original_size, f"Size mismatch: {len(reconstructed_data)} vs {original_size}"
    assert reconstructed_data == bytearray(original_bin_data), "Reconstructed data does not match original"

    output_path = tmp_path / "reconstructed_comms.bin"
    with open(output_path, "wb") as f:
        f.write(reconstructed_data)

    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) == original_size

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

    for i, (orig, recon) in enumerate(zip(original_packets, reconstructed_packets)):
        assert orig == recon, f"Packet {i} mismatch after comms transmission"


def test_comms_check_rq_file_params(sd_root):
    """Test file parameter validation."""
    dh._HOME_PATH = str(sd_root)
    file_tag = "thermal"

    DH.register_file_process(tag_name=file_tag, buffer_size=512)
    file_process = DH.data_process_registry[file_tag]

    test_data = bytearray([1, 2, 3] * 50)
    DH.log_file(file_tag, test_data)
    DH.file_completed(file_tag)

    filepath = file_process.current_path

    SATELLITE_RADIO.filepath = filepath
    SATELLITE_RADIO.file_get_metadata()

    valid_packet = SATELLITE_RADIO.file_ID.to_bytes(1, "big") + SATELLITE_RADIO.file_time.to_bytes(4, "big")
    assert SATELLITE_RADIO.check_rq_file_params(valid_packet) is True

    invalid_id_packet = (0xFF).to_bytes(1, "big") + SATELLITE_RADIO.file_time.to_bytes(4, "big")
    assert SATELLITE_RADIO.check_rq_file_params(invalid_id_packet) is False

    invalid_time_packet = SATELLITE_RADIO.file_ID.to_bytes(1, "big") + (0xDEADBEEF).to_bytes(4, "big")
    assert SATELLITE_RADIO.check_rq_file_params(invalid_time_packet) is False


if __name__ == "__main__":
    pytest.main()
