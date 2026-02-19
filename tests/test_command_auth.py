import hashlib
import hmac


from flight.apps.comms.auth import compute_hmac_sha256, get_auth_key_bytes, verify_authenticated_command


def _build_authenticated_packet(nonce, key):
    md_payload = bytes([64, 7])   # this is a request tm hal command
    nonce_payload = nonce + md_payload
    mac = compute_hmac_sha256(key, nonce_payload)

    return mac + nonce + md_payload


def test_hmac_matches_python_stdlib():
    key = bytes.fromhex("0b" * 20)
    message = b"Hi There"
    expected = hmac.new(key, message, hashlib.sha256).digest()

    assert compute_hmac_sha256(key, message) == expected


def test_verify_authenticated_command_success():
    key = bytes.fromhex("00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff")
    nonce = bytes.fromhex("01020304")

    packet = _build_authenticated_packet(nonce, key)
    ok, reason, new_packet = verify_authenticated_command(packet, key)

    assert ok is True
    assert reason == "auth_passed"
    assert len(new_packet) == len(packet) - 36


def test_verify_authenticated_command_fails_on_mac_mismatch():
    key = bytes.fromhex("00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff")
    nonce = bytes.fromhex("aabbccdd")

    packet = bytearray(_build_authenticated_packet(nonce, key))
    packet[1] ^= 0x01

    ok, reason, command_args = verify_authenticated_command(bytes(packet), key)

    assert ok is False
    assert reason == "mac_mismatch"
    assert command_args is None


def test_verify_authenticated_command_fails_on_length_mismatch():
    key = bytes.fromhex("00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff")
    nonce = b"\x00\x00\x00\x01"
    packet = _build_authenticated_packet(nonce, key)

    ok, reason, command_args = verify_authenticated_command(packet[10:], key)

    assert ok is False
    assert reason == "packet_too_short_for_authentication"
    assert command_args is None


def test_get_auth_key_bytes_validation():
    assert get_auth_key_bytes("") is None
    assert get_auth_key_bytes("not-hex") is None
    assert get_auth_key_bytes("aa" * 31) is None
    assert get_auth_key_bytes("aa" * 32) == bytes.fromhex("aa" * 32)
