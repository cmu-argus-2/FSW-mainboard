"""
PR comments: See corresponding issue.

Here, testing the shape output is good but you want to test the computation as well with a clear input value (no random values)
and compare it to your reference output to make sure the computation is correct.

You want also to test nominal cases and corner cases (near zero) or when a zero norm appears somewhere.
"""


import numpy as np
import pytest

import tests.cp_mock  # noqa: F401
from flight.apps.adcs.mcm import (
    MCMConst,
    ControllerHandler,
    MagneticCoilAllocator,
    get_spin_stabilizing_dipole_moment,
    get_sun_pointing_dipole_moment,
)


@pytest.fixture
def inputs() -> dict:
    return {
        "magnetic_field": np.array([1.0, 0.0, 0.0]),
        "sun_vector": np.array([1.0, 0.0, 0.0]),
        "spin_error": np.zeros(3),
        "pointing_error": np.zeros(3),
        "dipole_moment": np.zeros(3),
    }


@pytest.fixture
def outputs() -> dict:
    return {
        "spin_stabilizing_dipole_moment": np.zeros(3),
        "sun_pointing_dipole_moment": np.zeros(3),
    }


def test_spin_stabilizing(
    inputs,
    outputs,
) -> None:
    dipole_moment = get_spin_stabilizing_dipole_moment(
        inputs["magnetic_field"],
        inputs["spin_error"],
    )
    assert dipole_moment.shape == (3,)
    assert all(dipole_moment[i] == outputs["spin_stabilizing_dipole_moment"][i] for i in range(3))


def test_sun_pointing(
    inputs,
    outputs,
) -> None:
    dipole_moment = get_sun_pointing_dipole_moment(inputs["sun_vector"], inputs["pointing_error"])
    assert dipole_moment.shape == (3,)
    assert all(dipole_moment[i] == outputs["sun_pointing_dipole_moment"][i] for i in range(3))


def test_controller_handler() -> None:
    assert ControllerHandler.u_max.shape == (3,)
    assert ControllerHandler.spin_axis.shape == (3,)
    assert ControllerHandler.ang_vel_reference.shape == (3,)
    assert type(ControllerHandler.momentum_target) is float or type(ControllerHandler.momentum_target) is np.float64

    ControllerHandler.update_max_dipole_moment()
    assert ControllerHandler.u_max.shape == (3,)


def test_allocator(inputs) -> None:
    assert len(MagneticCoilAllocator._Vs_ctrl.items()) == 6
    for face, voltage in MagneticCoilAllocator._Vs_ctrl.items():
        assert type(face) is str or type(face) is np.str_
        assert type(voltage) is float or type(voltage) is np.float64

    MagneticCoilAllocator.set_voltages(inputs["dipole_moment"])

    assert len(MagneticCoilAllocator._Vs_ctrl.items()) == 6
    for face, voltage in MagneticCoilAllocator._Vs_ctrl.items():
        assert type(face) is str
        assert type(voltage) is float or type(voltage) is np.float64
        assert voltage == 0.0


@pytest.fixture
def parallel_inputs() -> dict:
    return {
        "magnetic_field": np.array([1.0, 0.0, 0.0]),
        "spin_error": np.array([1.0, 0.0, 0.0]),
        "pointing_error": np.array([1.0, 0.0, 0.0]),
    }


def test_spin_stabilizing_near_zero(parallel_inputs) -> None:
    # Check for NaN, which may occur when the argument vectors are parallel
    dipole_moment = get_spin_stabilizing_dipole_moment(parallel_inputs["magnetic_field"], parallel_inputs["spin_error"])
    assert dipole_moment.shape == (3,)
    assert not np.any(np.isnan(dipole_moment))


def test_sun_pointing_near_zero(parallel_inputs) -> None:
    # Check for NaN, which may occur when the argument vectors are parallel
    dipole_moment = get_spin_stabilizing_dipole_moment(parallel_inputs["magnetic_field"], parallel_inputs["pointing_error"])
    assert dipole_moment.shape == (3,)
    assert not np.any(np.isnan(dipole_moment))
