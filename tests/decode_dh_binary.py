#!/usr/bin/env python3
"""
Decode a DataHandler-formatted binary (DHGEN + fixed 242B records) back into the
original raw binary payload stream.

Usage:
    python decode_dh_binary.py <input_dh_file> <output_raw_file>
Defaults:
    input  = tests/image_radio_file_dh.bin
    output = tests/image_radio_file_raw.bin
"""
import os
import sys

# Add project paths
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "flight"))

import tests.cp_mock  # noqa: E402,F401
import core.data_handler as dh  # noqa: E402


def decode_dh_file(input_path: str, output_path: str) -> None:
    header_magic = dh._DH_MAGIC_NUMBER
    fixed_packet_size = dh._FIXED_PACKET_SIZE
    packet_header_size = dh._PACKET_HEADER_SIZE
    max_payload = dh._MAX_PAYLOAD_SIZE

    print(f"Decoding DH file: {input_path}")
    with open(input_path, "rb") as f:
        blob = f.read()

    if len(blob) < len(header_magic):
        raise RuntimeError("Input too small to contain DH magic")
    if blob[: len(header_magic)] != header_magic:
        raise RuntimeError("DH magic not found at start of file")

    offset = len(header_magic)
    packets = 0
    raw_bytes = bytearray()

    while offset < len(blob):
        if offset + fixed_packet_size > len(blob):
            print(f"WARNING: Truncated packet at offset {offset}, stopping.")
            break

        packet = blob[offset : offset + fixed_packet_size]
        if len(packet) < packet_header_size:
            print(f"WARNING: Incomplete header at offset {offset}, stopping.")
            break

        packet_len = int.from_bytes(packet[0:2], "big")
        if packet_len == 0 or packet_len > max_payload:
            print(f"WARNING: Invalid packet length {packet_len} at offset {offset}, stopping.")
            break

        payload_end = packet_header_size + packet_len
        if payload_end > fixed_packet_size:
            print(f"WARNING: Payload overruns fixed packet at offset {offset}, stopping.")
            break

        raw_bytes.extend(packet[packet_header_size:payload_end])
        packets += 1
        offset += fixed_packet_size

    with open(output_path, "wb") as out:
        out.write(raw_bytes)

    print(f"Decoded {packets} packets")
    print(f"Raw payload bytes: {len(raw_bytes)}")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    default_input = os.path.join(os.path.dirname(__file__), "image_radio_file_dh.bin")
    default_output = os.path.join(os.path.dirname(__file__), "image_radio_file_raw.bin")

    input_file = sys.argv[1] if len(sys.argv) > 1 else default_input
    output_file = sys.argv[2] if len(sys.argv) > 2 else default_output

    if not os.path.exists(input_file):
        print(f"ERROR: Input file not found: {input_file}")
        sys.exit(1)

    decode_dh_file(input_file, output_file)
