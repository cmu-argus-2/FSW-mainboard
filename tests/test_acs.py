import pytest

import tests.cp_mock  # noqa: F401
from flight.apps.adcs.consts import PhysicalConst, ControllerConst
from flight.apps.adcs.acs import (
    spin_stabilizing_controller,
    sun_pointed_controller,
    mcm_coil_allocator,
    zero_all_coils,
)
from ulab import numpy as np


@pytest.fixture
def zero_error_omega() -> np.ndarray:
    return ControllerConst.MOMENTUM_TARGET * np.linalg.inv(PhysicalConst.INERTIA_MAT) @ PhysicalConst.INERTIA_MAJOR_DIR


@pytest.fixture
def larger_error_omega(zero_error_omega: np.ndarray) -> np.ndarray:
    return 2 * zero_error_omega


@pytest.fixture
def nominal_mag_field() -> np.ndarray:
    return np.ones(3)


@pytest.mark.parametrize(
    "omega, mag_field, expected",
    [
        (   # zero error test case
            "zero_error_omega",
            "nominal_mag_field",
            np.zeros(3),
        ),
        (   # parallel readings test case
            "larger_error_omega",
            "zero_error_omega",
            np.zeros(3),
        ),
    ]
)
def test_nominal_spin_stabilization(
    omega: np.ndarray,
    mag_field: np.ndarray,
    expected: np.ndarray,
    request: pytest.FixtureRequest
) -> None:
    omega = request.getfixturevalue(omega)
    mag_field = request.getfixturevalue(mag_field)
    result = spin_stabilizing_controller(omega, mag_field)
    assert result == pytest.approx(expected, abs=1e-6)
