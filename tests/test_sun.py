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
        ([100, 0, 2900, 1100, 0, _ERROR_LUX, 0, 1000, 1800], (StatusConst.SUN_ECLIPSE, np.zeros((3,)))),
        # Random vectors and errors from MATLAB
        (
            [8.7307e04, 0, 0, 5.7749e03, 0, 1.3901e05, 7.3195e04, 1.5543e04, 8.1362e04],  # All sensors active
            (StatusConst.OK, np.array([0.6236, -0.0412, 0.7806])),
        ),
        (
            [0, 1.2325e05, _ERROR_LUX, 5.1884e04, 0, 0, 0, 1.1645e05, 6.5985e04],  # 1 sensor not working
            (StatusConst.OK, np.array([-0.8804, -0.3706, 0.2959])),
        ),
        (
            [0, 8.7216e04, _ERROR_LUX, 7.6500e04, _ERROR_LUX, 0, 1.3197e03, 1.1708e05, 1.0951e05],  # 2 not working
            (StatusConst.OK, np.array([-0.6230, -0.5464, 0.5598])),
        ),
        (
            [_ERROR_LUX, 6.8659e04, 7.2462e04, 0, _ERROR_LUX, 2.0860e04, _ERROR_LUX, 1.1796e05, 1.8171e04],  # 3 not working
            (StatusConst.OK, np.array([-0.4904, 0.5176, 0.7011])),
        ),
        (
            [_ERROR_LUX, _ERROR_LUX, 2.2247e04, _ERROR_LUX, 0, _ERROR_LUX, 8.1732e04, 0, 5.0270e04],  # No readings along X-axis
            (StatusConst.SUN_NOT_ENOUGH_READINGS, np.zeros((3,))),
        ),
        (
            [0, _ERROR_LUX, 3.8006e04, _ERROR_LUX, _ERROR_LUX, _ERROR_LUX, _ERROR_LUX, 9.6227e04, 6.8397e04],  # 5 not working
            (StatusConst.OK, np.array([-0.0096, 0.2715, 0.9624])),
        ),
        (
            [_ERROR_LUX, _ERROR_LUX, _ERROR_LUX, _ERROR_LUX, _ERROR_LUX, 0, _ERROR_LUX, 8.0155e04, 0],  # No readings along X
            (StatusConst.SUN_NOT_ENOUGH_READINGS, np.zeros((3,))),
        ),
    ],
)
def test_compute_body_sun_vector_from_lux(I_vec, expected):
    status, sun_pos = compute_body_sun_vector_from_lux(I_vec)
    assert status == expected[0]
    assert sun_pos == pytest.approx(expected[1], rel=1e-2)  # 7e-2 error on each axis corresponds to a 10 deg error in sun vec


if __name__ == "__main__":
    pytest.main()
