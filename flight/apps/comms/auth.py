from core import hashlib as _hashlib

AUTH_NONCE_SIZE = 4
AUTH_MAC_SIZE = 32
AUTH_TRAILER_SIZE = AUTH_NONCE_SIZE + AUTH_MAC_SIZE
_SHA256_BLOCK_SIZE = 64


def get_auth_key_bytes(auth_key_hex):
    if not auth_key_hex:
        return None

    try:
        key_bytes = bytes.fromhex(auth_key_hex)
    except ValueError:
        return None

    if len(key_bytes) != AUTH_MAC_SIZE:
        return None

    return key_bytes


def _sha256_digest(data):
    try:
        hasher = _hashlib.sha256()
    except AttributeError:
        hasher = _hashlib.new("sha256")

    hasher.update(data)
    return hasher.digest()


def compute_hmac_sha256(key, message):
    if len(key) > _SHA256_BLOCK_SIZE:
        key = _sha256_digest(key)

    if len(key) < _SHA256_BLOCK_SIZE:
        key = key + (b"\x00" * (_SHA256_BLOCK_SIZE - len(key)))

    o_key_pad = bytes((value ^ 0x5C) for value in key)
    i_key_pad = bytes((value ^ 0x36) for value in key)

    return _sha256_digest(o_key_pad + _sha256_digest(i_key_pad + message))


def constant_time_compare(left, right):
    if len(left) != len(right):
        return False

    result = 0

    for left_byte, right_byte in zip(left, right):
        result |= left_byte ^ right_byte

    return result == 0


def verify_authenticated_command(packet, auth_key):
    if auth_key is None:
        return False, "missing_or_invalid_auth_key", None
    
    if len(packet) < 36:
        return False, "packet_too_short_for_authentication", None
    
    nonce = packet[0:4]  # the next 4 bytes are the nonce, which is used for authentication
    received_mac = packet[4:36]  # the next 32 bytes are the mac, which is used for authentication
    cmd_payload = packet[36:]  # remove the auth info from the packet 

    message = cmd_payload + nonce
    computed_mac = compute_hmac_sha256(auth_key, message)

    if not constant_time_compare(computed_mac, received_mac):
        return False, "mac_mismatch", None

    return True, "auth_passed", cmd_payload
