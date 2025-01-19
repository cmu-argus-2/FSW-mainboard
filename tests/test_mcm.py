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
    ControllerHandler,
    MagneticCoilAllocator,
    get_spin_stabilizing_dipole_moment,
    get_sun_pointing_dipole_moment,
)


@pytest.fixture
def readings() -> dict:
    sun_vector = np.random.uniform(size=3)
    magnetic_field = np.random.uniform(size=3)
    spin_error = np.random.uniform(size=3)
    pointing_error = np.random.uniform(size=3)
    dipole_moment = np.random.uniform(size=3)
    return {
        "sun_vector": sun_vector,
        "magnetic_field": magnetic_field,
        "spin_error": spin_error,
        "pointing_error": pointing_error,
        "dipole_moment": dipole_moment,
    }


def test_spin_stabilizing(readings) -> None:
    dipole_moment = get_spin_stabilizing_dipole_moment(
        readings["magnetic_field"],
        readings["spin_error"],
    )
    assert dipole_moment.shape == (3,)


def test_sun_pointing(readings) -> None:
    dipole_moment = get_sun_pointing_dipole_moment(
        readings["sun_vector"],
        readings["pointing_error"],
    )
    assert dipole_moment.shape == (3,)


def test_controller_handler() -> None:
    assert ControllerHandler.u_max.shape == (3,)
    assert ControllerHandler.spin_axis.shape == (3,)
    assert ControllerHandler.ang_vel_reference.shape == (3,)
    assert type(ControllerHandler.momentum_target) is float or type(ControllerHandler.momentum_target) is np.float64

    ControllerHandler.update_max_dipole_moment()
    assert ControllerHandler.u_max.shape == (3,)


def test_allocator(readings) -> None:
    assert len(MagneticCoilAllocator._Vs_ctrl.items()) == 6
    for face, voltage in MagneticCoilAllocator._Vs_ctrl.items():
        assert type(face) is str or type(face) is np.str_
        assert type(voltage) is float or type(voltage) is np.float64

    MagneticCoilAllocator.set_voltages(readings["dipole_moment"])

    assert len(MagneticCoilAllocator._Vs_ctrl.items()) == 6
    for face, voltage in MagneticCoilAllocator._Vs_ctrl.items():
        assert type(face) is str
        assert type(voltage) is float or type(voltage) is np.float64
