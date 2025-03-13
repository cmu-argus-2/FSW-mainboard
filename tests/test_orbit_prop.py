import pytest
import numpy as np

from flight.apps.adcs.orbit_propagation import OrbitPropagator
from flight.apps.adcs.consts import StatusConst

# NOTE: All these tests run on ISS orbit since they have the most amount of publicly available data
"""
    TESTS WITHOUT INITIALIZATION
    In these tests, no valid GPS reading is provided to orbit prop

    Tests checked:
    1. NoneType GPS state
    3. NoneType last_gps_time
    4. Incorrect length of GPS state
    5. Invalid GPS position, valid GPS velocity
    6. Invalid GPS velocity, valid GPS position
"""


def initialize_orbit_prop():
    gps_state = np.array(
        [-3219374.639793210, -5571639.458031840, 2188968.931596490, 3394.57407891549, -4129.24891352844, -5485.70643668604]
    )
    status, pos, vel = OrbitPropagator.propagate_orbit(1741622400, 1741622400, gps_state)
    assert OrbitPropagator.initialized


# NoneType GPS
@pytest.mark.parametrize(
    "current_time, last_gps_time, last_gps_state_eci, expected",
    [
        (  # NoneType GPS state
            13456,  # Random chosen times
            13453,
            None,
            (StatusConst.OPROP_INIT_FAIL, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]),
        ),
        (
            # NoneType current time
            None,
            13453,
            None,
            (StatusConst.OPROP_INIT_FAIL, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]),
        ),
        (
            # NoneType gps time
            13456,
            None,
            None,
            (StatusConst.OPROP_INIT_FAIL, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]),
        ),
        (
            # Incorrect state size
            13456,
            13453,
            np.array([-321937.4639793210, -557163.9458031840, 218896.8931596490, 3394.57407891549, -4129.24891352844]),
            (StatusConst.OPROP_INIT_FAIL, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]),
        ),
        (
            # Invalid position (position provided in km)
            13456,
            13453,
            np.array(
                [
                    -3219.374639793210,
                    -5571.639458031840,
                    2188.968931596490,
                    3.39457407891549,
                    -4.12924891352844,
                    -5.48570643668604,
                ]
            ),
            (StatusConst.OPROP_INIT_FAIL, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]),
        ),
        (
            # Invalid gps velocity (velocity in km/s)
            13456,
            None,
            np.array(
                [
                    -3219374.639793210,
                    -5571639.458031840,
                    2188968.931596490,
                    3.39457407891549,
                    -4.12924891352844,
                    -5.48570643668604,
                ]
            ),
            (StatusConst.OPROP_INIT_FAIL, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]),
        ),
    ],
)
def test_orbit_prop(current_time, last_gps_time, last_gps_state_eci, expected):
    status, position, velocity = OrbitPropagator.propagate_orbit(current_time, last_gps_time, last_gps_state_eci)
    assert (
        status == expected[0]
        and position == pytest.approx(expected[1], rel=1e-6)
        and velocity == pytest.approx(expected[2], rel=1e-6)
    )


"""
    TESTS WITH INITIALIZATION

    Tests checked:
    1. NoneType GPS state
    3. NoneType last_gps_time
    4. Incorrect length of GPS state
    5. Invalid GPS position, valid GPS velocity
    6. Invalid GPS velocity, valid GPS position
"""


# NoneType GPS
@pytest.mark.parametrize(
    "current_time, last_gps_time, last_gps_state_eci, expected",
    [
        (  # NoneType GPS state
            1741622640,
            13453,
            None,
            (
                StatusConst.OK,
                np.array([-2297524.851622470, -6348054.288460810, 808627.939779857]),
                np.array([4240.56803838024, -2301.49126346825, -5946.69715389632]),
            ),
        ),
        (None, 13453, None, (StatusConst.OPROP_INIT_FAIL, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0])),  # NoneType current time
        (
            # NoneType gps time
            1741622640,
            None,
            np.array(
                [
                    -3219374.639793210,
                    -5571639.458031840,
                    2188968.931596490,
                    3394.57407891549,
                    -4129.24891352844,
                    -5485.70643668604,
                ]
            ),
            (
                StatusConst.OK,
                np.array([-2297524.851622470, -6348054.288460810, 808627.939779857]),
                np.array([4240.56803838024, -2301.49126346825, -5946.69715389632]),
            ),
        ),
        (
            # Incorrect state size
            1741624080,
            1741622640,
            np.array([-3219374.639793210, -5571639.458031840, 2188968.931596490, 3394.57407891549, -4129.24891352844]),
            (
                StatusConst.OK,
                np.array([3880237.884662470, -1722334.024225960, -5313147.785300470]),
                np.array([2376.19387476277, 7245.70026396382, -607.57360024516]),
            ),
        ),
        (
            # Invalid position (position provided in km)
            1741624080,
            1741622640,
            np.array(
                [
                    -3219374.639793210,
                    -5571639.458031840,
                    2188968.931596490,
                    3.39457407891549,
                    -4.12924891352844,
                    -5.48570643668604,
                ]
            ),
            (
                StatusConst.OK,
                np.array([3880237.884662470, -1722334.024225960, -5313147.785300470]),
                np.array([2376.19387476277, 7245.70026396382, -607.57360024516]),
            ),
        ),
    ],
)
def test_orbit_prop_initialized(current_time, last_gps_time, last_gps_state_eci, expected):
    initialize_orbit_prop()
    status, position, velocity = OrbitPropagator.propagate_orbit(current_time, last_gps_time, last_gps_state_eci)
    assert (
        status == expected[0]
        and position == pytest.approx(expected[1], rel=2e3)
        and velocity == pytest.approx(expected[2], rel=10)
    )
