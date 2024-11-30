import pytest

from flight.apps.adcs.mcm import (
    ControllerHandler,
    MagneticCoilAllocator,
    get_b_cross_dipole_moment,
    get_pd_sun_pointing_dipole_moment,
)
from ulab import numpy as np


@pytest.fixture
def readings() -> dict:
    sun_vector = np.random.uniform(size=3)
    magnetic_field = np.random.uniform(size=3)
    magnetic_field_norm = np.linalg.norm(magnetic_field)
    angular_velocity = np.random.uniform(size=3)
    angular_momentum = np.random.uniform(size=3)
    dipole_moment = np.random.uniform(size=3)
    return {
        "sun_vector": sun_vector,
        "magnetic_field": magnetic_field,
        "magnetic_field_norm": magnetic_field_norm,
        "angular_velocity": angular_velocity,
        "angular_momentum": angular_momentum,
        "dipole_moment": dipole_moment,
    }


def test_b_cross(readings) -> None:
    dipole_moment = get_b_cross_dipole_moment(
        readings["magnetic_field"],
        readings["magnetic_field_norm"],
        readings["angular_velocity"],
    )
    assert dipole_moment.shape == (3,)


def test_pd_sun_pointing(readings) -> None:
    dipole_moment = get_pd_sun_pointing_dipole_moment(
        readings["sun_vector"],
        readings["magnetic_field"],
        readings["magnetic_field_norm"],
        readings["angular_velocity"],
    )
    assert dipole_moment.shape == (3,)


def test_controller_handler(readings) -> None:
    assert ControllerHandler.spin_axis.shape == (3,)
    assert ControllerHandler.ang_vel_reference.shape == (3,)
    assert type(ControllerHandler._h_norm_target) is float or type(ControllerHandler._h_norm_target) is np.float64

    is_spin_stable = ControllerHandler.is_spin_stable(readings["angular_momentum"])
    assert type(is_spin_stable) is bool or type(is_spin_stable) is np.bool_

    is_sun_pointing = ControllerHandler.is_sun_pointing(
        readings["sun_vector"],
        readings["angular_momentum"],
    )
    assert type(is_sun_pointing) is bool or type(is_sun_pointing) is np.bool_


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
