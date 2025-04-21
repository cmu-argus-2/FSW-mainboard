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
            [7.8592e4, 0, 5.0082e4, 0, 1.2945e5, 1.0929e5, 1.8302e4, 3.8461e4, 0],  # All sensors active
            (StatusConst.OK, np.array([0.5614, 0.3577, 0.7463])),
        ),
        (
            [6.3769e4, 0, 1.2443e5, 0, _ERROR_LUX, 8.2945e4, 0, 0, 7.1272e3],  # 1 sensor not working
            # [6.3769e4, 0, 1.2443e5, 0, 4.0051e4, 8.2945e4, 0, 0, 7.1272e3]
            (StatusConst.OK, np.array([0.4555, 0.8888, -0.0509])),
        ),
        (
            [0, 8.8434e4, 1.0842e5, _ERROR_LUX, 0, 7.3230e4, _ERROR_LUX, 0, 4.8603e3],  # 2 not working
            # [0, 8.8434e4, 1.0842e5, 0, 0, 7.3230e4, 5.9095e4, 0, 4.8603e3]
            (StatusConst.OK, np.array([-0.6317, 0.7745, -0.0347])),
        ),
        (
            [_ERROR_LUX, 0, _ERROR_LUX, _ERROR_LUX, 1.0644e5, 6.3273e3, 2.8399e4, 1.2851e5, 0],  # 3 not working
            # [5.5182e4, 0, 0, 8.6397e4, 1.0644e5, 6.3273e3, 2.8399e4, 1.2851e5, 0]
            (StatusConst.OK, np.array([0.3942, -0.6171, 0.6810])),
        ),
        (
            [1.3277e4, _ERROR_LUX, 1.2641e5, 0, _ERROR_LUX, _ERROR_LUX, _ERROR_LUX, 0, 0],  # No readings along Y-axis
            # [1.3277e4, 0, 1.2641e5, 0, 5.0877e4, 1.3088e5, 3.2110e4, 0, 0]
            (StatusConst.SUN_NOT_ENOUGH_READINGS, np.zeros((3,))),  # [0.0948, 0.9029, 0.4192]
        ),
        (
            [_ERROR_LUX, _ERROR_LUX, 4.9293e4, 0, _ERROR_LUX, _ERROR_LUX, _ERROR_LUX, 3.3240e4, 0],  # 5 not working
            # [0, 8.8861e4, 4.9293e4, 0, 5.2616e3, 1.0295e5, 1.3093e5, 3.3240e4, 0]
            (StatusConst.SUN_NOT_ENOUGH_READINGS, np.zeros((3,))),  # [-0.6347, 0.3521, 0.6879]
        ),
        (
            [_ERROR_LUX, _ERROR_LUX, _ERROR_LUX, 1.1010e4, _ERROR_LUX, _ERROR_LUX, _ERROR_LUX, 9.0691e4, 0],  # 6 not working
            # [0, 7.5708e4, 0, 1.1010e4, 2.9373e4, 7.5121e4, 1.3644e5, 9.0691e4, 0]
            (StatusConst.SUN_NOT_ENOUGH_READINGS, np.zeros((3,))),  # [-0.5408, -0.0786, 0.8375]
        ),
    ],
)
def test_compute_body_sun_vector_from_lux(I_vec, expected):
    status, sun_pos = compute_body_sun_vector_from_lux(I_vec)
    assert status == expected[0]
    assert sun_pos == pytest.approx(expected[1], abs=1e-2)  # 7e-2 error on each axis corresponds to a 10 deg error in sun vec


if __name__ == "__main__":
    pytest.main()
