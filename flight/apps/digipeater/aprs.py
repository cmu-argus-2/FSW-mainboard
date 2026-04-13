"""LoRa APRS plain-text packet validation and digipeating for satellite relay.

LoRa APRS packet wire format:
    [0x3C] [0xFF] [0x01] <ASCII APRS string>

APRS string (TNC-2 monitor format):
    CALLSIGN>TOCALL,token1,token2,...:payload

Digipeating replaces the first un-digipeated WIDEn-N token (n >= 1, N >= 1)
in the path with CALLSIGN* (asterisk marks the hop as completed).
"""

_LORA_APRS_HEADER = b"\x3c\xff\x01"
_HEADER_LEN = 3


def is_valid_lora_aprs_packet(data):
    """Return True if data is a structurally valid LoRa APRS packet."""
    if not data or len(data) < _HEADER_LEN + 1:
        return False
    if data[:_HEADER_LEN] != _LORA_APRS_HEADER:
        return False
    try:
        aprs_str = data[_HEADER_LEN:].decode("ascii")
    except (UnicodeDecodeError, ValueError):
        return False
    gt_idx = aprs_str.find(">")
    if gt_idx < 1:
        return False
    colon_idx = aprs_str.find(":", gt_idx + 1)
    if colon_idx < 0:
        return False
    return True


def _is_eligible_wide_token(token):
    """Return True if token is an un-digipeated WIDEn-N token (N >= 1)."""
    if token.endswith("*"):
        return False
    upper = token.upper()
    if not upper.startswith("WIDE"):
        return False
    rest = upper[4:]
    if len(rest) != 3:
        return False
    n_char, dash, hop_char = rest[0], rest[1], rest[2]
    if dash != "-":
        return False
    if not n_char.isdigit() or not hop_char.isdigit():
        return False
    if int(hop_char) < 1:
        return False
    return True


def build_digipeated_packet(data, callsign):
    """Replace first eligible WIDEn-N path token with callsign*.

    Returns the modified packet as bytes, or None if no eligible token found.
    """
    if not data or len(data) < _HEADER_LEN + 1:
        return None
    if data[:_HEADER_LEN] != _LORA_APRS_HEADER:
        return None
    try:
        aprs_str = data[_HEADER_LEN:].decode("ascii")
    except (UnicodeDecodeError, ValueError):
        return None
    gt_idx = aprs_str.find(">")
    if gt_idx < 1:
        return None
    colon_idx = aprs_str.find(":", gt_idx + 1)
    if colon_idx < 0:
        return None

    src_and_gt = aprs_str[: gt_idx + 1]                  # "CALLSIGN>"
    tocall_and_path = aprs_str[gt_idx + 1 : colon_idx]   # "TOCALL,token,..."
    payload = aprs_str[colon_idx:]                        # ":...payload..."

    parts = tocall_and_path.split(",")                    # [TOCALL, token, token, ...]
    replaced = False
    new_parts = [parts[0]]                                # keep TOCALL unchanged
    for token in parts[1:]:
        if not replaced and _is_eligible_wide_token(token):
            new_parts.append(callsign + "*")
            replaced = True
        else:
            new_parts.append(token)

    if not replaced:
        return None

    new_aprs_str = src_and_gt + ",".join(new_parts) + payload
    return _LORA_APRS_HEADER + new_aprs_str.encode("ascii")
