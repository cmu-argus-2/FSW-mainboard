import numpy as np
import pytest

import tests.cp_mock  # noqa: F401
from flight.apps.adcs.consts import StatusConst
from flight.apps.adcs.sun import _ERROR_LUX, compute_body_sun_vector_from_lux


@pytest.mark.parametrize(
    "I_vec, expected",
    [
        # NO Readings
        ([_ERROR_LUX] * 9, (StatusConst.SUN_NO_READINGS, np.zeros((3,)))),
        # Not enough Readings
        ([90000, 35000] + [_ERROR_LUX] * 7, (StatusConst.SUN_NOT_ENOUGH_READINGS, np.zeros((3,)))),
        # Eclipse
        ([100, 0, 2900, 1100, _ERROR_LUX, 0, 1000, 1800, 0], (StatusConst.SUN_ECLIPSE, np.zeros((3,)))),
        # Random vectors and errors from MATLAB
        (
            [7.8592e4, 0, 5.0082e4, 0, 1.2945e5, 1.0929e5, 7.3875e4, 7.3875e4, 0],  # All sensors active
            (StatusConst.OK, np.array([0.5614, 0.3577, 0.7463])),
        ),
        (
            [_ERROR_LUX, 0, 1.2443e5, 0, 4.5091e4, 8.7984e4, 0, 0, 7.1272e3],  # 1 sensor not working
            (StatusConst.OK, np.array([0.4555, 0.8888, -0.0509])),
        ),
        (
            [0, 8.8434e4, 1.0842e5, _ERROR_LUX, 0, _ERROR_LUX, 6.2532e4, 0, 4.8603e3],  # 2 not working
            (StatusConst.OK, np.array([-0.6317, 0.7745, -0.0347])),
        ),
        (
            [5.5182e4, 0, _ERROR_LUX, 8.6397e4, _ERROR_LUX, 6.7418e3, _ERROR_LUX, 1.2851e5, 0],  # 3 not working
            (StatusConst.OK, np.array([0.3942, -0.6171, 0.6810])),
        ),
        (
            [1.3277e4, 0, _ERROR_LUX, _ERROR_LUX, _ERROR_LUX, _ERROR_LUX, 4.1499e4, 4.1499e4, 0],  # No readings along Y-axis
            (StatusConst.SUN_NOT_ENOUGH_READINGS, np.zeros((3,))),
        ),
        (
            [0, _ERROR_LUX, 4.9293e4, _ERROR_LUX, _ERROR_LUX, _ERROR_LUX, _ERROR_LUX, 6.8095e4, 0],  # 5 not working
            (StatusConst.SUN_NOT_ENOUGH_READINGS, np.zeros((3,))),
        ),
        (
            [0, _ERROR_LUX, _ERROR_LUX, _ERROR_LUX, _ERROR_LUX, _ERROR_LUX, _ERROR_LUX, 9.0691e4, 0],  # No readings along X
            (StatusConst.SUN_NOT_ENOUGH_READINGS, np.zeros((3,))),
        ),
    ],
)
def test_compute_body_sun_vector_from_lux(I_vec, expected):
    status, sun_pos = compute_body_sun_vector_from_lux(I_vec)
    assert status == expected[0]
    assert sun_pos == pytest.approx(expected[1], abs=1e-2)  # 7e-2 error on each axis corresponds to a 10 deg error in sun vec


if __name__ == "__main__":
    pytest.main()
