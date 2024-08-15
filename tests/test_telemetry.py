import pytest
from flight.apps.telemetry.helpers import (
    convert_float_to_fixed_point_lp,
    convert_fixed_point_to_float_lp,
    convert_float_to_fixed_point_hp,
    convert_fixed_point_to_float_hp,
)


@pytest.mark.parametrize(
    "val, expected",
    [
        (32767.9999, bytearray([0x7F, 0xFF, 0xFF, 0xF9])),
        (-32767.9999, bytearray([0xFF, 0xFF, 0xFF, 0xF9])),
        (0.5, bytearray([0x00, 0x00, 0x80, 0x00])),
        (-0.5, bytearray([0x80, 0x00, 0x80, 0x00])),
        (12345.6789, bytearray([0x30, 0x39, 0xAD, 0xCC])),
    ],
)
def test_convert_float_to_fixed_point_lp(val, expected):
    result = convert_float_to_fixed_point_lp(val)
    assert result == expected


@pytest.mark.parametrize(
    "message_list, expected",
    [
        ([0x7F, 0xFF, 0xFF, 0xFF], 32767.9999),
        ([0xFF, 0xFF, 0xFF, 0xFF], -32767.9999),
        ([0x00, 0x00, 0x80, 0x00], 0.5),
        ([0x80, 0x00, 0x80, 0x00], -0.5),
        ([0x30, 0x39, 0xAD, 0xF9], 12345.6789),
    ],
)
def test_convert_fixed_point_to_float_lp(message_list, expected):
    result = convert_fixed_point_to_float_lp(message_list)
    assert result == pytest.approx(expected, rel=1e-5)


@pytest.mark.parametrize(
    "val, expected",
    [
        (128.9999999, bytearray([0x00, 0xFF, 0xFF, 0xFE])),
        (-128.9999999, bytearray([0x80, 0xFF, 0xFF, 0xFE])),
        (0.5, bytearray([0x00, 0x80, 0x00, 0x00])),
        (-0.5, bytearray([0x80, 0x80, 0x00, 0x00])),
        (12.3456789, bytearray([0x0C, 0x58, 0x7E, 0x69])),
    ],
)
def test_convert_float_to_fixed_point_hp(val, expected):
    result = convert_float_to_fixed_point_hp(val)
    assert result == expected


@pytest.mark.parametrize(
    "message_list, expected",
    [
        ([0x7F, 0xFF, 0xFF, 0xFF], 127.9999999),
        ([0xFF, 0xFF, 0xFF, 0xFF], -127.9999999),
        ([0x00, 0x80, 0x00, 0x00], 0.5),
        ([0x80, 0x80, 0x00, 0x00], -0.5),
        ([0x0C, 0x58, 0x7E, 0x69], 12.3456789),
    ],
)
def test_convert_fixed_point_to_float_hp(message_list, expected):
    result = convert_fixed_point_to_float_hp(message_list)
    assert result == pytest.approx(expected, rel=1e-6)
