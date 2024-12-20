"""
Magnetic Control Module.
Includes magnetorquer controllers for spin stabilizing and sun pointing,
controller reference handler, and magnetorquer voltage allocator.

Author(s): Derek Fan
"""

import copy
from typing import Tuple

from apps.adcs.consts import MagnetorquerConst, MCMConst, ModeConst, PhysicalConst
from apps.adcs.math import is_near
from hal.configuration import SATELLITE
from ulab import numpy as np


def get_spin_stabilizing_dipole_moment(
    magnetic_field: np.ndarray,
    spin_error: np.ndarray,
) -> np.ndarray:
    """
    B-cross law: https://arc.aiaa.org/doi/epdf/10.2514/1.53074.
    Augmented with tanh function for soft clipping.
    All sensor estimates are in the body-fixed reference frame.
    """
    u_dir = MCMConst.SPIN_STABILIZING_GAIN * np.cross(magnetic_field, spin_error)
    return ControllerHandler.u_max * np.tanh(u_dir)


def get_sun_pointing_dipole_moment(
    magnetic_field: np.ndarray,
    pointing_error: np.ndarray,
) -> np.ndarray:
    """
    Bang-bang sun pointing slewing law.
    All sensor estimates are in the body-fixed reference frame.
    """
    u_dir = np.cross(magnetic_field, pointing_error)
    u_dir_norm = np.linalg.norm(u_dir)

    # Check for zeros to prevent division by zero
    if is_near(u_dir_norm, 0.0):
        return np.zeros(3)
    else:
        return ControllerHandler.u_max * u_dir / u_dir_norm


class ControllerHandler:
    """
    "Handler" for determining controller references.
    """

    # Max dipole moment computed from max voltage
    u_max = np.zeros(3)

    # Max dipole moment conversion factor
    _u_max_convert = MagnetorquerConst.V_MAX / MagnetorquerConst.V_CONVERT

    # Init spin direction
    _eigvals, _eigvecs = np.linalg.eig(PhysicalConst.INERTIA_MAT)
    _unscaled_axis = _eigvecs[:, np.argmax(_eigvals)]
    spin_axis = _unscaled_axis / np.linalg.norm(_unscaled_axis)
    if spin_axis[np.argmax(np.abs(spin_axis))] < 0:
        spin_axis = -spin_axis

    # References and targets
    ang_vel_reference = spin_axis * MCMConst.REF_FACTOR * ModeConst.STABLE_TOL
    # ang_vel_target = np.linalg.norm(ang_vel_reference)
    momentum_target = np.linalg.norm(PhysicalConst.INERTIA_MAT @ ang_vel_reference)

    @classmethod
    def update_max_dipole_moment(cls) -> None:
        cls.u_max[:] = 0  # Reset the existing array in place
        for row in MagneticCoilAllocator.mat:
            if not np.all(row == 0.0):
                row_norm = np.linalg.norm(row)
                cls.u_max += row / row_norm * cls._u_max_convert


class MagneticCoilAllocator:
    """
    Dipole moment-to-voltage allocator.
    """

    _Vs_ctrl = {
        "XP": 0.0,
        "XM": 0.0,
        "YP": 0.0,
        "YM": 0.0,
        "ZP": 0.0,
        "ZM": 0.0,
    }

    mat = copy.deepcopy(MCMConst.ALLOC_MAT)

    _sat = SATELLITE

    @classmethod
    def set_voltages(
        cls,
        dipole_moment: np.ndarray,
    ) -> None:
        cls._update_matrix()
        ControllerHandler.update_max_dipole_moment()

        Vs = MagnetorquerConst.V_CONVERT * cls.mat @ dipole_moment
        Vs_bd = np.clip(Vs, -MagnetorquerConst.V_MAX, MagnetorquerConst.V_MAX)

        # print("\n", "VOLTAGES:", Vs_bd, "\n")

        for axis, face_idx in MCMConst.AXIS_FACE_INDICES.items():
            cls._Vs_ctrl[axis + "P"] = Vs_bd[face_idx["P"]]
            cls._Vs_ctrl[axis + "M"] = Vs_bd[face_idx["M"]]
        cls._sat.APPLY_MAGNETIC_CONTROL(cls._Vs_ctrl)

    @classmethod
    def _coils_on_axis_are_available(
        cls,
        axis: str,
    ) -> Tuple[bool, bool]:
        P_avail = cls._sat.TORQUE_DRIVERS_AVAILABLE(axis + "P")
        M_avail = cls._sat.TORQUE_DRIVERS_AVAILABLE(axis + "M")
        return P_avail, M_avail

    @classmethod
    def _update_matrix(cls) -> None:
        for axis, face_idx in MCMConst.AXIS_FACE_INDICES.items():
            P_avail, M_avail = cls._coils_on_axis_are_available(axis)

            # Different combinations of active coils
            if P_avail and M_avail:
                cls.mat[face_idx["P"]] = MCMConst.ALLOC_MAT[face_idx["P"]]
                cls.mat[face_idx["M"]] = MCMConst.ALLOC_MAT[face_idx["M"]]

            elif P_avail and not M_avail:
                cls.mat[face_idx["P"]] = 2 * MCMConst.ALLOC_MAT[face_idx["P"]]
                cls.mat[face_idx["M"]] = np.zeros(3)

            elif not P_avail and M_avail:
                cls.mat[face_idx["P"]] = np.zeros(3)
                cls.mat[face_idx["M"]] = 2 * MCMConst.ALLOC_MAT[face_idx["M"]]

            elif not P_avail and not M_avail:
                cls.mat[face_idx["P"]] = np.zeros(3)
                cls.mat[face_idx["M"]] = np.zeros(3)
