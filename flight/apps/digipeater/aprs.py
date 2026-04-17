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
    if not data or len(data) < _HEADER_LEN + 1:
        return 1

    # try an decode using ascii
    try:
        aprs_str = data[_HEADER_LEN:].decode("ascii")
    except (UnicodeDecodeError, ValueError):
        return 3

    # use re_obj to check if the satellite callsing is in the string
    result = re_obj.search(aprs_str)
    if result is None:
        return 4

    # ind max size: 10 (because of ssid)
    # dst max size: 6
    # extra chars: header + > = 4
    # the maximum distance from the beggining of the string should be 20
    # check if the callsign is in the first 20 characters of the string
    if result.start() > 20:
        return 5

    return 6

def add_asterisk_packet(data, re_obj):
    """
    Will simply add an asterisk to the end of callsign in the path to indicate that the packed has been repeated
    """
    return re_obj.sub(r"\g<0>*", data)
