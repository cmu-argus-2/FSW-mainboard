import pytest

import tests.cp_mock  # noqa: F401
from flight.apps.adcs.sun import ERROR_LUX, SUN_VECTOR_STATUS, compute_body_sun_vector_from_lux, in_eclipse


@pytest.mark.parametrize(
    "I_vec, expected",
    [
        (
            [80000, 0, 30000, 0, 0],
            (
                SUN_VECTOR_STATUS.UNIQUE_DETERMINATION,
                [0.93632918, 0.35112344, 0.0],
            ),
        ),
        (
            [117000, 0, 0, 0, 0],
            (SUN_VECTOR_STATUS.UNIQUE_DETERMINATION, [1.0, 0.0, 0.0]),
        ),
        (
            [0, 117000, 0, 0, 0],
            (SUN_VECTOR_STATUS.UNIQUE_DETERMINATION, [-1.0, 0.0, 0.0]),
        ),
        (
            [0, 0, 117000, 0, 0],
            (SUN_VECTOR_STATUS.UNIQUE_DETERMINATION, [0.0, 1.0, 0.0]),
        ),
        (
            [0, 0, 0, 117000, 0],
            (SUN_VECTOR_STATUS.UNIQUE_DETERMINATION, [0.0, -1.0, 0.0]),
        ),
        (
            [0, 0, 0, 0, 117000],
            (SUN_VECTOR_STATUS.UNIQUE_DETERMINATION, [0.0, 0.0, 1.0]),
        ),
        (
            [ERROR_LUX, 117000, 0, 0, 0],
            (SUN_VECTOR_STATUS.MISSING_XP_READING, [-1.0, 0, 0]),
        ),
        (
            [0, ERROR_LUX, 0, 117000, 0],
            (SUN_VECTOR_STATUS.MISSING_XM_READING, [0.0, -1.0, 0.0]),
        ),
        (
            [ERROR_LUX, 20000, 0, ERROR_LUX, ERROR_LUX],
            (SUN_VECTOR_STATUS.NOT_ENOUGH_READINGS, [-1.0, 0.0, 0.0]),
        ),
        (
            [ERROR_LUX, ERROR_LUX, ERROR_LUX, ERROR_LUX, ERROR_LUX],
            (SUN_VECTOR_STATUS.NO_READINGS, [0.0, 0.0, 0.0]),
        ),
    ],
)
def test_compute_body_sun_vector_from_lux(I_vec, expected):
    result = compute_body_sun_vector_from_lux(I_vec)
    assert result[0] == expected[0]
    assert result[1] == pytest.approx(expected[1], rel=1e-6)


@pytest.mark.parametrize(
    "raw_readings, threshold_lux_illumination, expected",
    [
        (
            [2000, 3000, 2500, 4000, 3500],
            1000,
            False,
        ),  # All readings are above threshold
        (
            [500, 600, 700, 400, 550],
            5000,
            True,
        ),  # All readings are below threshold
        (
            [2000, 300, 2500, 400, 3500],
            1000,
            False,
        ),  # Aboove and below threshold
        (
            [ERROR_LUX, ERROR_LUX, ERROR_LUX, ERROR_LUX, ERROR_LUX],
            1000,
            False,
        ),  # All readings are ERROR_LUX
    ],
)
def test_in_eclipse(raw_readings, threshold_lux_illumination, expected):
    assert in_eclipse(raw_readings, threshold_lux_illumination) == expected


if __name__ == "__main__":
    pytest.main()
