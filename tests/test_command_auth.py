import hashlib
import hmac

from flight.apps.comms.auth import AUTH_TRAILER_SIZE, compute_hmac_sha256, get_auth_key_bytes, verify_authenticated_command


def _build_authenticated_packet(cmd_id, sq_cnt, args_bytes, nonce, key):
    md_payload = bytes([cmd_id]) + sq_cnt.to_bytes(2, "big") + bytes([len(args_bytes)]) + args_bytes
    mac_message = bytes([cmd_id]) + md_payload + nonce
    mac = compute_hmac_sha256(key, mac_message)
    return md_payload + nonce + mac


def test_hmac_matches_python_stdlib():
    key = bytes.fromhex("0b" * 20)
    message = b"Hi There"
    expected = hmac.new(key, message, hashlib.sha256).digest()

    assert compute_hmac_sha256(key, message) == expected


def test_verify_authenticated_command_success():
    key = bytes.fromhex("00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff")
    cmd_id = 0x41
    sq_cnt = 0
    args = bytes([0x02]) + (30).to_bytes(4, "big")
    nonce = bytes.fromhex("01020304")

    packet = _build_authenticated_packet(cmd_id, sq_cnt, args, nonce, key)
    ok, reason, command_args = verify_authenticated_command(packet, cmd_id, len(args), key)

    assert ok is True
    assert reason == "auth_passed"
    assert command_args == args
    assert len(packet) == 4 + len(args) + AUTH_TRAILER_SIZE


def test_verify_authenticated_command_fails_on_mac_mismatch():
    key = bytes.fromhex("00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff")
    cmd_id = 0x42
    sq_cnt = 5
    args = (1735689600).to_bytes(4, "big")
    nonce = bytes.fromhex("aabbccdd")

    packet = bytearray(_build_authenticated_packet(cmd_id, sq_cnt, args, nonce, key))
    packet[-1] ^= 0x01

    ok, reason, command_args = verify_authenticated_command(bytes(packet), cmd_id, len(args), key)

    assert ok is False
    assert reason == "mac_mismatch"
    assert command_args is None


def test_verify_authenticated_command_fails_on_length_mismatch():
    key = bytes.fromhex("00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff")
    cmd_id = 0x40
    args = b""
    nonce = b"\x00\x00\x00\x01"
    packet = _build_authenticated_packet(cmd_id, 0, args, nonce, key)

    ok, reason, command_args = verify_authenticated_command(packet[:-1], cmd_id, len(args), key)

    assert ok is False
    assert reason == "authenticated_packet_length_mismatch"
    assert command_args is None


def test_get_auth_key_bytes_validation():
    assert get_auth_key_bytes("") is None
    assert get_auth_key_bytes("not-hex") is None
    assert get_auth_key_bytes("aa" * 31) is None
    assert get_auth_key_bytes("aa" * 32) == bytes.fromhex("aa" * 32)
