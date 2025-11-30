#!/usr/bin/env python3
# isort: skip_file
"""
Script to process a binary file with custom packet structure through DataHandler's FileProcess.
This reads a binary file (like image_radio_file.bin) with custom packet headers and stores
it using DataHandler's packet format (ARGUS header + fixed-size packets).
"""
import os
import sys
import struct
import tempfile
from dataclasses import dataclass

# Add project paths
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "flight"))

import tests.cp_mock  # noqa: E402 F401
import core.data_handler as dh  # noqa: E402
from core.data_handler import DataHandler as DH  # noqa: E402


@dataclass
class PacketHeader:
    """Custom packet header structure matching the binary file format."""

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


def process_custom_binary(input_path: str, output_path: str):
    """
    Process a binary file with custom packet structure through DataHandler.

    Args:
        input_path: Path to input binary file (e.g., image_radio_file.bin)
        output_path: Path to save the DataHandler-formatted output
    """

    # Read the input binary file
    print(f"Reading input file: {input_path}")
    with open(input_path, "rb") as f:
        original_bin_data = f.read()

    original_size = len(original_bin_data)
    print(f"Input file size: {original_size} bytes")

    # Create temporary directory for DataHandler
    with tempfile.TemporaryDirectory() as tmpdir:
        dh._HOME_PATH = tmpdir
        file_tag = "radio_img"

        # Register file process
        DH.register_file_process(tag_name=file_tag, buffer_size=512)
        file_process = DH.data_process_registry[file_tag]

        # Calculate max data per packet for FileProcess
        max_data_size = dh._FIXED_PACKET_SIZE - dh._PACKET_HEADER_SIZE  # 240 bytes

        print("\nParsing custom packets from input file...")
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

            print(
                f"  Packet {len(original_packets) - 1}: page_id={header.page_id}, "
                f"tile_idx={header.tile_idx}, frag_idx={header.frag_idx}, "
                f"payload_size={header.payload_size_bytes} bytes"
            )

            offset = payload_end

        print(f"\nFound {len(original_packets)} custom packets in input file")

        # Store each custom packet through DataHandler
        print("\nStoring packets through DataHandler...")
        dh_packet_count = 0
        for i, packet_data in enumerate(original_packets):
            # Check if this packet fits in one FileProcess packet
            if len(packet_data) <= max_data_size:
                # Fits in one packet - store as is
                DH.log_file(file_tag, bytearray(packet_data))
                dh_packet_count += 1
            else:
                # Need to split across multiple FileProcess packets
                pkt_offset = 0
                while pkt_offset < len(packet_data):
                    chunk_size = min(max_data_size, len(packet_data) - pkt_offset)
                    chunk = bytearray(packet_data[pkt_offset : pkt_offset + chunk_size])
                    DH.log_file(file_tag, chunk)
                    dh_packet_count += 1
                    pkt_offset += chunk_size

        print(f"Stored as {dh_packet_count} DataHandler packets")

        # Complete the file (flush buffer)
        DH.file_completed(file_tag)

        # Get the created file path
        created_file = file_process.current_path
        print(f"\nDataHandler file created at: {created_file}")

        # Verify file structure
        file_size = os.path.getsize(created_file)
        print(f"Output file size: {file_size} bytes")
        print(f"  = {dh._DH_FILE_HEADER_SIZE} bytes (ARGUS header)")
        print(f"  + {dh_packet_count} × {dh._FIXED_PACKET_SIZE} bytes (fixed packets)")
        expected_size = dh._DH_FILE_HEADER_SIZE + dh_packet_count * dh._FIXED_PACKET_SIZE
        print(f"  = {expected_size} bytes")

        # Copy to output location
        with open(created_file, "rb") as src:
            file_data = src.read()
            with open(output_path, "wb") as dst:
                dst.write(file_data)

        print(f"\n✓ DataHandler binary file saved to: {output_path}")

        # Verify we can reconstruct the original data
        print("\nVerifying reconstruction...")
        reconstructed_data = bytearray()
        for i in range(dh_packet_count):
            result = file_process.get_packet(created_file, i)
            if result:
                length, data = result
                reconstructed_data.extend(data)
            else:
                print(f"  ERROR: Could not retrieve packet {i}")
                return

        # Verify reconstructed data matches original
        if len(reconstructed_data) == original_size:
            print(f"✓ Reconstruction size matches: {original_size} bytes")
        else:
            print(f"✗ Size mismatch: {len(reconstructed_data)} vs {original_size} bytes")
            return

        if reconstructed_data == bytearray(original_bin_data):
            print("✓ Reconstructed data matches original perfectly")
        else:
            print("✗ Reconstructed data does not match original")
            return

        # Parse reconstructed data to verify custom packets
        print("\nVerifying custom packet structure in reconstructed data...")
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

        if len(reconstructed_packets) == len(original_packets):
            print(f"✓ Custom packet count matches: {len(original_packets)} packets")
        else:
            print(f"✗ Packet count mismatch: {len(reconstructed_packets)} vs {len(original_packets)}")
            return

        # Verify each packet matches
        all_match = True
        for i, (orig, recon) in enumerate(zip(original_packets, reconstructed_packets)):
            if orig != recon:
                print(f"✗ Packet {i} mismatch")
                all_match = False

        if all_match:
            print("✓ All custom packets match perfectly")

        print("\n" + "=" * 70)
        print("SUCCESS! Binary file processed and verified.")
        print(f"Input:  {input_path}")
        print(f"Output: {output_path}")
        print("=" * 70)


if __name__ == "__main__":
    # Default input/output locations
    input_file = os.path.join(os.path.dirname(__file__), "image_radio_file.bin")
    output_file = os.path.join(os.path.dirname(__file__), "image_radio_file_dh.bin")

    # Allow custom paths as command line arguments
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"ERROR: Input file not found: {input_file}")
        print(f"\nUsage: {sys.argv[0]} [input_file] [output_file]")
        print("  input_file:  Binary file with custom packet structure (default: image_radio_file.bin)")
        print("  output_file: Output DataHandler binary file (default: image_radio_file_dh.bin)")
        sys.exit(1)

    print("Processing binary file through DataHandler...")
    print("=" * 70)
    process_custom_binary(input_file, output_file)
