"""AX.25 frame validation and header modification for digipeater relay.

AX.25 UI frame structure:
    [Dest (7)] [Src (7)] [Digi0..N (7 each)] [Control (1)] [PID (1)] [Info (var)]

Each address entry is 7 bytes:
    - 6 bytes: callsign characters (ASCII left-shifted 1 bit, space-padded)
    - 1 byte SSID: H | R | R | SSID(4) | Extension
        H = has-been-repeated (digipeater addresses only)
        R = reserved (set to 1)
        SSID = 4-bit secondary station ID
        Extension = 1 if this is the last address, 0 otherwise
"""

_AX25_ADDR_LEN = 7  # bytes per address entry
_AX25_MIN_ADDRS = 2  # destination + source
_AX25_MIN_FRAME = _AX25_MIN_ADDRS * _AX25_ADDR_LEN + 2  # + control + PID
_AX25_MAX_DIGIS = 8  # protocol maximum


def _find_address_end(data):
    """Return the byte offset just past the last address entry, or None."""
    for i in range(_AX25_ADDR_LEN - 1, len(data), _AX25_ADDR_LEN):
        if data[i] & 0x01:  # extension bit set = last address
            return i + 1
    return None


def is_valid_ax25_frame(data):
    """Check if raw bytes form a valid AX.25 UI frame.

    Returns True if the frame has a well-formed address field
    (at least destination + source) followed by control and PID bytes.
    """
    if not data or len(data) < _AX25_MIN_FRAME:
        return False

    addr_end = _find_address_end(data)
    if addr_end is None:
        return False

    # Address field must contain at least dest + src (14 bytes)
    if addr_end < _AX25_MIN_ADDRS * _AX25_ADDR_LEN:
        return False

    # Number of addresses must be a whole multiple of 7
    if addr_end % _AX25_ADDR_LEN != 0:
        return False

    # Must have at least control + PID after addresses
    if len(data) < addr_end + 2:
        return False

    return True


def _encode_ax25_address(callsign, ssid=0, last=False, h_bit=True):
    """Encode a callsign into a 7-byte AX.25 address entry.

    Args:
        callsign: Up to 6 ASCII characters.
        ssid: Secondary station ID (0-15).
        last: If True, set the extension bit (marks end of address field).
        h_bit: If True, set the has-been-repeated bit.
    """
    # Pad callsign to 6 characters with spaces, then left-shift each byte
    padded = (callsign.upper() + "      ")[:6]
    addr = bytearray(7)
    for i in range(6):
        addr[i] = ord(padded[i]) << 1

    # SSID byte: H | 1 | 1 | SSID(4) | Extension
    ssid_byte = 0x60  # reserved bits set (0b01100000)
    ssid_byte |= (ssid & 0x0F) << 1
    if h_bit:
        ssid_byte |= 0x80
    if last:
        ssid_byte |= 0x01
    addr[6] = ssid_byte

    return bytes(addr)


def add_digipeater_to_via_path(data, callsign):
    """Insert satellite callsign into the AX.25 via-path with H-bit set.

    Appends the satellite as the last digipeater in the repeater path,
    marking it as already-repeated (H=1).

    Returns modified frame bytes, or None if the frame cannot be modified.
    """
    addr_end = _find_address_end(data)
    if addr_end is None:
        return None

    num_addrs = addr_end // _AX25_ADDR_LEN
    if num_addrs >= _AX25_MAX_DIGIS + _AX25_MIN_ADDRS:
        # Via-path is full, cannot add another digipeater
        return None

    # Build modified frame:
    # 1. Copy existing addresses but clear extension bit on the old last entry
    modified = bytearray(data[:addr_end])
    modified[addr_end - 1] &= 0xFE  # clear extension bit on old last address

    # 2. Append satellite callsign as new last address with H-bit and extension bit set
    digi_entry = _encode_ax25_address(callsign, ssid=0, last=True, h_bit=True)
    modified.extend(digi_entry)

    # 3. Append the rest of the frame (control + PID + info)
    modified.extend(data[addr_end:])

    return bytes(modified)
