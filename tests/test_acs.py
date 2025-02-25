import pytest

import tests.cp_mock  # noqa: F401
from flight.apps.adcs.consts import PhysicalConst, ControllerConst
from flight.apps.adcs.acs import (
    spin_stabilizing_controller,
    sun_pointing_controller,
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


@pytest.mark.parametrize(
    "omega, mag_field, expected",
    [
        (   # zero error test case
            "zero_error_omega",
            np.ones(3),
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
    # Get fixture values
    if type(omega) == str:
        omega = request.getfixturevalue(omega)
    if type(mag_field) == str:
        mag_field = request.getfixturevalue(mag_field)
    # Assert controller output value
    result = spin_stabilizing_controller(omega, mag_field)
    assert result.shape == (3,)
    assert result == pytest.approx(expected, abs=1e-6)


@pytest.fixture
def invalid_dims() -> list[int]:
    return [0, 1, 2, 4, 5, 6, 7, 8, 9]


@pytest.mark.parametrize(
    "valid_omega, valid_mag_field, expected",
    [
        (   # Expect zero control
            np.ones(3),
            np.ones(3),
            np.zeros(3),
        ),
    ]
)
def test_invalid_dim_spin_stabilization(
    valid_omega: np.ndarray,
    valid_mag_field: np.ndarray,
    expected: np.ndarray,
    invalid_dims: list[int],
) -> None:
    for i in invalid_dims:
        # Test angular velocity with invalid dimensions
        invalid_omega = np.ones(i)
        result = spin_stabilizing_controller(invalid_omega, valid_mag_field)
        assert result == pytest.approx(expected, abs=1e-6)
        # Test magnetic field with invalid dimensions
        invalid_mag_field = np.ones(i)
        result = spin_stabilizing_controller(valid_omega, invalid_mag_field)
        assert result == pytest.approx(expected, abs=1e-6)
