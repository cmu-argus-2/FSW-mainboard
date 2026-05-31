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


def is_valid_lora_aprs_packet(data, re_obj):
    """Return True if data is a structurally valid LoRa APRS packet."""

    # check if there are enough bytes
    if len(data) < _HEADER_LEN + 9:  # header + minimum APRS string length
        return 1

    # try an decode using ascii
    try:
        aprs_str = data[_HEADER_LEN:].decode("ascii")
    except (UnicodeDecodeError, ValueError):
        return 2

    return 4 if re_obj.match(aprs_str) else 3


def add_asterisk_packet(data, re_obj):
    """
    Will simply add an asterisk to the end of callsign in the path to indicate that the packed has been repeated
    """
    return re_obj.sub(r"\g<0>*", data)
