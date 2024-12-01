"""
Attitude Determination and Control Subsystem (ADCS)
Magnetic Control Module
"""

import copy
from typing import Tuple

from apps.adcs.consts import MagnetorquerConst, MCMConst, PhysicalConst
from apps.adcs.math import skew
from hal.configuration import SATELLITE
from ulab import numpy as np


def get_b_cross_dipole_moment(
    magnetic_field: np.ndarray,
    magnetic_field_norm: float,
    angular_velocity: np.ndarray,
) -> np.ndarray:
    """
    B-cross law: https://arc.aiaa.org/doi/epdf/10.2514/1.53074.
    All sensor estimates are in the body-fixed reference frame.
    """
    unit_field = magnetic_field / magnetic_field_norm
    ang_vel_err = ControllerHandler.ang_vel_reference - angular_velocity
    return -MCMConst.BCROSS_GAIN * np.cross(unit_field, ang_vel_err)


def get_pd_sun_pointing_dipole_moment(
    sun_vector: np.ndarray,
    magnetic_field: np.ndarray,
    magnetic_field_norm: float,
    angular_velocity: np.ndarray,
) -> np.ndarray:
    Bhat_pinv = skew(magnetic_field).T / magnetic_field_norm**2
    att_angvel_err = np.hstack(
        (
            -ControllerHandler.spin_axis - sun_vector,
            ControllerHandler.ang_vel_reference - angular_velocity,
        )
    )
    return Bhat_pinv @ MCMConst.PD_GAINS @ att_angvel_err


class ControllerHandler:
    """
    "Handler" for determining controller modes and references.
    """

    # Init spin direction
    _eigvals, _eigvecs = np.linalg.eig(PhysicalConst.INERTIA_MAT)
    spin_axis = _eigvecs[:, np.argmax(_eigvals)]
    if spin_axis[np.argmax(np.abs(spin_axis))] < 0:
        spin_axis = -spin_axis

    ang_vel_reference = spin_axis * MCMConst.ANG_VEL_NORM_TARGET
    _h_norm_target = np.linalg.norm(PhysicalConst.INERTIA_MAT @ ang_vel_reference)

    @classmethod
    def is_spin_stable(
        self,
        angular_momentum: np.ndarray,
    ) -> bool:
        spin_err = np.linalg.norm(self.spin_axis - (angular_momentum / self._h_norm_target))
        return spin_err < MCMConst.ANG_VEL_NORM_THRESHOLD

    @classmethod
    def is_sun_pointing(
        self,
        sun_vector: np.ndarray,
        angular_momentum: np.ndarray,
    ) -> bool:
        h_norm = np.linalg.norm(angular_momentum)
        pointing_err = np.linalg.norm(sun_vector - (angular_momentum / h_norm))
        return pointing_err < MCMConst.ANG_VEL_NORM_TARGET


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

    _mat = copy.deepcopy(MCMConst.ALLOC_MAT)

    _sat = SATELLITE

    @classmethod
    def set_voltages(
        self,
        dipole_moment: np.ndarray,
    ) -> None:
        self._update_matrix()
        Vs = MagnetorquerConst.V_CONVERT * self._mat @ dipole_moment
        Vs_bd = np.clip(Vs, -MagnetorquerConst.V_MAX, MagnetorquerConst.V_MAX)

        for axis, face_idx in MCMConst.AXIS_FACE_INDICES.items():
            self._Vs_ctrl[axis + "P"] = Vs_bd[face_idx["P"]]
            self._Vs_ctrl[axis + "M"] = Vs_bd[face_idx["M"]]
        self._sat.APPLY_MAGNETIC_CONTROL(self._Vs_ctrl)

    @classmethod
    def _coils_on_axis_are_available(
        self,
        axis: str,
    ) -> Tuple[bool, bool]:
        P_avail = self._sat.TORQUE_DRIVERS_AVAILABLE(axis + "P")
        M_avail = self._sat.TORQUE_DRIVERS_AVAILABLE(axis + "M")
        return P_avail, M_avail

    @classmethod
    def _update_matrix(self) -> None:
        for axis, face_idx in MCMConst.AXIS_FACE_INDICES.items():
            P_avail, M_avail = self._coils_on_axis_are_available(axis)

            # Different combinations of active coils
            if P_avail and M_avail:
                self._mat[face_idx["P"]] = MCMConst.ALLOC_MAT[face_idx["P"]]
                self._mat[face_idx["M"]] = MCMConst.ALLOC_MAT[face_idx["M"]]

            elif P_avail and not M_avail:
                self._mat[face_idx["P"]] = 2 * MCMConst.ALLOC_MAT[face_idx["P"]]
                self._mat[face_idx["M"]] = np.zeros(3)

            elif not P_avail and M_avail:
                self._mat[face_idx["P"]] = np.zeros(3)
                self._mat[face_idx["M"]] = 2 * MCMConst.ALLOC_MAT[face_idx["M"]]

            elif not P_avail and not M_avail:
                self._mat[face_idx["P"]] = np.zeros(3)
                self._mat[face_idx["M"]] = np.zeros(3)
