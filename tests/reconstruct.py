import io
import os
import struct
import sys
from dataclasses import dataclass
from typing import List, Dict, Tuple
from collections import defaultdict
from PIL import Image

INPUT_BIN = "image_radio_file_raw.bin"
INPUT_META = "img_0.meta"
OUTPUT_IMAGE_PNG = "tilepack/gs_reconstructed.png"
TILES_OUTPUT_DIR = "tilepack/gs_reconstructed_tiles"

ASPECT_RATIO_WIDTH = 4
ASPECT_RATIO_HEIGHT = 3
DEFAULT_TILE_WIDTH = 64
DEFAULT_TILE_HEIGHT = 32


@dataclass
class PacketHeader:
    payload_size_bytes: int
    page_id: int
    tile_idx: int
    frag_idx: int

    @staticmethod
    def from_bytes(data: bytes) -> "PacketHeader":
        """Parse header from 7 bytes"""
        if len(data) < 7:
            raise ValueError(f"Header data too short: {len(data)} bytes (need 7)")
        payload_size, page_id, tile_idx, frag_idx = struct.unpack(">HHHB", data[:7])
        return PacketHeader(payload_size, page_id, tile_idx, frag_idx)

    @staticmethod
    def size_bytes() -> int:
        return 7


@dataclass
class Packet:
    header: PacketHeader
    payload: bytes


@dataclass
class ImageMetadata:
    page_id: int
    tiles_x: int
    tiles_y: int
    tile_w: int
    tile_h: int
    target_width: int
    target_height: int
    jpeg_quality: int

    @staticmethod
    def from_file(filepath: str) -> "ImageMetadata":
        with open(filepath, "rb") as f:
            data = f.read()
        if len(data) < 15:
            raise ValueError(f"Metadata file too short: {len(data)} bytes")

        page_id, tiles_x, tiles_y, tile_w, tile_h, target_w, target_h, quality = struct.unpack(">HHHHHHHB", data[:15])
        return ImageMetadata(page_id, tiles_x, tiles_y, tile_w, tile_h, target_w, target_h, quality)


def read_packets_from_bin(filepath: str) -> List[Packet]:
    packets = []
    hdr_size = PacketHeader.size_bytes()

    with open(filepath, "rb") as f:
        packet_idx = 0
        while True:
            hdr_data = f.read(hdr_size)
            if not hdr_data:
                break

            if len(hdr_data) < hdr_size:
                print(f"[WARNING] Incomplete header at packet {packet_idx}, skipping", file=sys.stderr)
                break

            header = PacketHeader.from_bytes(hdr_data)

            payload = f.read(header.payload_size_bytes)

            if len(payload) < header.payload_size_bytes:
                print(
                    f"[WARNING] Incomplete payload at packet {packet_idx} "
                    f"(expected {header.payload_size_bytes}, got {len(payload)})",
                    file=sys.stderr,
                )
                break

            packets.append(Packet(header=header, payload=payload))
            packet_idx += 1

    return packets


def group_fragments_by_tile(packets: List[Packet]) -> Dict[int, List[Tuple[int, bytes]]]:
    """
    Group packet fragments by tile_idx.
    Returns dict: tile_idx -> list of (frag_idx, payload) tuples
    Deduplicates fragments - keeps only the first occurrence of each (tile_idx, frag_idx) pair
    """
    tiles = defaultdict(dict)  # tile_idx -> {frag_idx: payload}

    for pkt in packets:
        tile_idx = pkt.header.tile_idx
        frag_idx = pkt.header.frag_idx

        # Only store the first occurrence of each fragment
        if frag_idx not in tiles[tile_idx]:
            tiles[tile_idx][frag_idx] = pkt.payload

    # Convert dict to sorted list of tuples
    result = {}
    for tile_idx, frags_dict in tiles.items():
        result[tile_idx] = sorted(frags_dict.items(), key=lambda x: x[0])

    return result


def reconstruct_tile_jpeg(
    fragments: List[Tuple[int, bytes]], tile_w: int, tile_h: int, tile_idx: int = -1
) -> Tuple[bytes, str]:
    """
    Reconstruct a tile JPEG from fragments.
    Returns (jpeg_bytes, status) where status is:
      'complete' - all fragments present
      'partial' - some fragments missing, JPEG may be corrupted but decodable
      'missing' - no fragments, black tile created
    """
    if not fragments:
        # No fragments, create a black tile
        black_tile = Image.new("RGB", (tile_w, tile_h), (0, 0, 0))
        bio = io.BytesIO()
        black_tile.save(bio, format="JPEG", quality=50)
        return bio.getvalue(), "missing"

    fragments_sorted = sorted(fragments, key=lambda x: x[0])

    # Check if fragments are consecutive (complete)
    actual_indices = [frag[0] for frag in fragments_sorted]

    # Check for missing fragments in the sequence
    max_frag_idx = max(actual_indices) if actual_indices else 0
    all_expected = list(range(max_frag_idx + 1))
    missing_frags = set(all_expected) - set(actual_indices)

    if missing_frags:
        # Partial fragments - concatenate what we have
        # The JPEG decoder might still decode partial data
        jpeg_bytes = b"".join(payload for _, payload in fragments_sorted)
        status = "partial"
        if tile_idx >= 0:
            print(f"    [WARNING] Tile {tile_idx} missing fragments {sorted(missing_frags)}, JPEG may be corrupted")
    else:
        # All fragments present
        jpeg_bytes = b"".join(payload for _, payload in fragments_sorted)
        status = "complete"

    return jpeg_bytes, status


def reconstruct_image(
    tiles_dict: Dict[int, bytes], tiles_x: int, tiles_y: int, tile_w: int, tile_h: int, target_width: int, target_height: int
) -> Image.Image:
    canvas = Image.new("RGB", (target_width, target_height), (0, 0, 0))

    expected_tiles = tiles_x * tiles_y
    failed_decode_tiles = []
    decoded_tiles = 0

    for tile_idx in range(expected_tiles):
        tx = tile_idx % tiles_x
        ty = tile_idx // tiles_x
        x = tx * tile_w
        y = ty * tile_h

        if tile_idx in tiles_dict:
            jpeg_bytes = tiles_dict[tile_idx]
            try:
                tile_img = Image.open(io.BytesIO(jpeg_bytes))
                canvas.paste(tile_img, (x, y))
                decoded_tiles += 1
            except Exception as e:
                print(f"[WARNING] Failed to decode tile {tile_idx}: {e}", file=sys.stderr)
                failed_decode_tiles.append(tile_idx)

    if failed_decode_tiles:
        print(
            f"[WARNING] {len(failed_decode_tiles)} tiles failed to decode (corrupted): {failed_decode_tiles[:10]}{'...' if len(failed_decode_tiles) > 10 else ''}"  # noqa: E501
        )

    print(f"Successfully decoded and placed {decoded_tiles}/{expected_tiles} tiles in final image")

    return canvas


def main():
    if not os.path.exists(INPUT_BIN):
        print(f"[ERROR] Binary file not found: {INPUT_BIN}", file=sys.stderr)
        sys.exit(1)

    metadata = None
    if os.path.exists(INPUT_META):
        try:
            metadata = ImageMetadata.from_file(INPUT_META)
            print(
                f"Loaded metadata: {metadata.tiles_x}x{metadata.tiles_y} tiles, "
                f"tile size {metadata.tile_w}x{metadata.tile_h}, "
                f"target {metadata.target_width}x{metadata.target_height}"
            )
        except Exception as e:
            print(f"[WARNING] Failed to load metadata: {e}", file=sys.stderr)
            print("Will attempt to infer dimensions from packets...")
    else:
        print(f"[INFO] Metadata file not found: {INPUT_META}")
        print("Will attempt to infer dimensions from packets...")

    print(f"Reading packets from: {INPUT_BIN}")
    packets = read_packets_from_bin(INPUT_BIN)
    print(f"Read {len(packets)} packets")

    if not packets:
        print("[ERROR] No packets found in binary file", file=sys.stderr)
        sys.exit(1)

    tiles_fragments = group_fragments_by_tile(packets)
    print(f"Found {len(tiles_fragments)} unique tiles")

    if metadata is None:
        if tiles_fragments:
            first_fragments = tiles_fragments[min(tiles_fragments.keys())]
            first_jpeg, _ = reconstruct_tile_jpeg(first_fragments, DEFAULT_TILE_WIDTH, DEFAULT_TILE_HEIGHT)
            first_tile = Image.open(io.BytesIO(first_jpeg))
            tile_w, tile_h = first_tile.size
        else:
            tile_w, tile_h = DEFAULT_TILE_WIDTH, DEFAULT_TILE_HEIGHT  # Default fallback
    else:
        tile_w = metadata.tile_w
        tile_h = metadata.tile_h

    # Reconstruct all tiles (fill missing with black, attempt partial reconstruction)
    if metadata:
        expected_tiles = metadata.tiles_x * metadata.tiles_y
    else:
        # Estimate based on what we have
        expected_tiles = max(tiles_fragments.keys()) + 1 if tiles_fragments else 0

    tiles_jpeg = {}
    missing_tile_count = 0
    partial_tile_count = 0
    complete_tile_count = 0

    for tile_idx in range(expected_tiles):
        if tile_idx in tiles_fragments:
            jpeg_bytes, status = reconstruct_tile_jpeg(tiles_fragments[tile_idx], tile_w, tile_h, tile_idx)

            if status == "complete":
                complete_tile_count += 1
                print(f"  Tile {tile_idx}: {len(tiles_fragments[tile_idx])} fragments -> {len(jpeg_bytes)} bytes [COMPLETE]")
            elif status == "partial":
                partial_tile_count += 1
                print(
                    f"  Tile {tile_idx}: {len(tiles_fragments[tile_idx])} fragments -> {len(jpeg_bytes)} bytes [PARTIAL - may be corrupted]"  # noqa: E501
                )
            else:  # missing (shouldn't happen here but handle it)
                missing_tile_count += 1
                print(f"  Tile {tile_idx}: MISSING (filled with black)")
        else:
            # Missing tile - create black JPEG
            jpeg_bytes, _ = reconstruct_tile_jpeg([], tile_w, tile_h, tile_idx)
            missing_tile_count += 1
            print(f"  Tile {tile_idx}: MISSING (filled with black)")

        tiles_jpeg[tile_idx] = jpeg_bytes

    print("\nTile reconstruction statistics:")
    print(f"  Complete tiles: {complete_tile_count}/{expected_tiles}")
    print(f"  Partial tiles (some fragments missing): {partial_tile_count}/{expected_tiles}")
    print(f"  Missing tiles (filled with black): {missing_tile_count}/{expected_tiles}")

    # Save individual tile JPEGs
    os.makedirs(TILES_OUTPUT_DIR, exist_ok=True)
    for tile_idx, jpeg_bytes in tiles_jpeg.items():
        tile_path = os.path.join(TILES_OUTPUT_DIR, f"tile_{tile_idx:05d}.jpg")
        with open(tile_path, "wb") as f:
            f.write(jpeg_bytes)
    print(f"Saved {len(tiles_jpeg)} individual tile JPEGs to {TILES_OUTPUT_DIR}/")

    if metadata is None:
        # Guess based on common tile sizes
        max_tile_idx = max(tiles_jpeg.keys())
        num_tiles = max_tile_idx + 1

        # Try common aspect ratios for VGA (640x480)
        # With 64x32 tiles: 10 tiles wide, 15 tiles tall = 150 tiles
        # With 32x32 tiles: 20 tiles wide, 15 tiles tall = 300 tiles

        first_tile = Image.open(io.BytesIO(tiles_jpeg[0]))
        tile_w, tile_h = first_tile.size

        tiles_x = int((num_tiles * ASPECT_RATIO_WIDTH / ASPECT_RATIO_HEIGHT) ** 0.5 * ASPECT_RATIO_HEIGHT / ASPECT_RATIO_WIDTH)
        tiles_y = (num_tiles + tiles_x - 1) // tiles_x

        target_width = tiles_x * tile_w
        target_height = tiles_y * tile_h

        print(
            f"[INFO] Inferred dimensions: {tiles_x}x{tiles_y} tiles, "
            f"tile size {tile_w}x{tile_h}, target {target_width}x{target_height}"
        )
    else:
        tiles_x = metadata.tiles_x
        tiles_y = metadata.tiles_y
        tile_w = metadata.tile_w
        tile_h = metadata.tile_h
        target_width = metadata.target_width
        target_height = metadata.target_height

    print(f"Reconstructing image ({target_width}x{target_height})...")
    img = reconstruct_image(tiles_jpeg, tiles_x, tiles_y, tile_w, tile_h, target_width, target_height)

    os.makedirs(os.path.dirname(OUTPUT_IMAGE_PNG) if os.path.dirname(OUTPUT_IMAGE_PNG) else ".", exist_ok=True)

    total_tile_bytes = sum(len(jpeg_data) for jpeg_data in tiles_jpeg.values())
    print("\nReconstruction summary:")
    print(f"  Total tile JPEGs: {total_tile_bytes} bytes ({total_tile_bytes / 1024:.1f} kB)")

    img.save(OUTPUT_IMAGE_PNG, format="PNG")
    png_size = os.path.getsize(OUTPUT_IMAGE_PNG)
    print(f"  Reconstructed PNG: {png_size} bytes ({png_size / 1024:.1f} kB)")
    print(f"  Saved: {OUTPUT_IMAGE_PNG}")
    print(f"      Individual tiles saved to: {TILES_OUTPUT_DIR}/")
    print(f"Image size: {img.size[0]}x{img.size[1]}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)
