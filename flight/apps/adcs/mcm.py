# Attitude Determination and Control Subsystem (ADCS)
# Magnetic Control Module


# TODO: implement controllers: B-dot, Bcross, Sun pointing
# TODO: implement desired moment allocation to voltages
# ...

# To apply the voltages to the coils, the following function is used:
# SATELLITE.APPLY_MAGNETIC_CONTROL({'XP': 5.0, 'XM': 5.1, 'YP': 4.8, 'YM': 5.0, 'ZP': 4.1, 'ZM': 4.1})

import copy
from typing import Tuple

from apps.adcs.consts import MCMConstants, PhysicalConstants
from apps.adcs.math import skew
from hal.configuration import SATELLITE
from ulab import numpy as np


class ControllerHandler:
    """ """

    # Init spin direction
    eigvals, eigvecs = np.linalg.eig(PhysicalConstants.INERTIA_TENSOR)
    spin_axis = eigvecs[:, np.argmax(eigvals)]
    if spin_axis[np.argmax(np.abs(spin_axis))] < 0:
        spin_axis = -spin_axis

    ang_vel_reference = spin_axis * MCMConstants.ANG_VEL_NORM_TARGET
    _h_norm_target = np.linalg.norm(PhysicalConstants.INERTIA_TENSOR @ ang_vel_reference)

    """
    @classmethod
    def _get_reused_values(
        self,
        magnetic_field: np.ndarray,
        angular_velocity: np.ndarray,
    ) -> Tuple[np.ndarray, float]:
        h = MCMConstants.J @ angular_velocity
        b_norm = np.linalg.norm(magnetic_field)
        return h, b_norm
    """

    @classmethod
    def is_spin_stable(
        self,
        angular_momentum: np.ndarray,
    ) -> bool:
        spin_err = np.linalg.norm(self.spin_axis - (angular_momentum / self._h_norm_target))
        return spin_err < MCMConstants.ANG_VEL_NORM_THRESHOLD

    @classmethod
    def is_sun_pointing(
        self,
        sun_vector: np.ndarray,
        angular_momentum: np.ndarray,
    ) -> bool:
        h_norm = np.linalg.norm(angular_momentum)
        pointing_err = np.linalg.norm(sun_vector - (angular_momentum / h_norm))
        return pointing_err < MCMConstants.ANG_VEL_NORM_TARGET

    """
    @classmethod
    def get_dipole_moment_command(
        self,
        sun_vector: np.ndarray,
        magnetic_field: np.ndarray,
        angular_velocity: np.ndarray,
    ) -> np.ndarray:
        h, b_norm = self._get_reused_values(magnetic_field, angular_velocity)

        if not self._is_spin_stable(h):
            return BCrossController.get_dipole_moment_command(magnetic_field, b_norm, angular_velocity)
        elif not self._is_sun_pointing(sun_vector, h):
            return PDSunPointingController.get_dipole_moment_command(sun_vector, magnetic_field, b_norm, angular_velocity)
        else:
            return np.zeros(3)
    """


class MagnetorquerController:
    """
    Template for magnetic dipole moment control.
    """

    def get_dipole_moment_command():
        raise NotImplementedError()


class BCrossController(MagnetorquerController):
    """
    B-cross law: https://arc.aiaa.org/doi/epdf/10.2514/1.53074.
    All sensor estimates are in the body-fixed reference frame.
    """

    @classmethod
    def get_dipole_moment_command(
        self,
        magnetic_field: np.ndarray,
        magnetic_field_norm: float,
        angular_velocity: np.ndarray,
    ) -> np.ndarray:
        unit_field = magnetic_field / magnetic_field_norm
        ang_vel_err = ControllerHandler.ang_vel_reference - angular_velocity
        return -MCMConstants.BCROSS_GAIN * np.cross(unit_field, ang_vel_err)


class PDSunPointingController(MagnetorquerController):
    """ """

    @classmethod
    def get_dipole_moment_command(
        self,
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
        return Bhat_pinv @ MCMConstants.PD_GAINS @ att_angvel_err


class MagneticCoilAllocator:
    """
    High-level voltage allocator.
    """

    _Vs_ctrl = {
        "XP": 0.0,
        "XM": 0.0,
        "YP": 0.0,
        "YM": 0.0,
        "zP": 0.0,
        "zM": 0.0,
    }

    _alloc_mat = copy.deepcopy(MCMConstants.ALLOCATION_MATRIX)

    _Vs_max = np.array([5.0, 5.0, 5.0, 5.0, 5.0, 5.0])

    _sat = SATELLITE

    @classmethod
    def set_voltages(
        self,
        dipole_moment: np.ndarray,
    ) -> None:
        self._update_matrix()
        Vs = self._alloc_mat @ dipole_moment
        Vs_bd = np.clip(Vs, -self._Vs_max, self._Vs_max)
        for axis, face_idx in MCMConstants.AXIS_FACE_INDICES.items():
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
        for axis, face_idx in MCMConstants.AXIS_FACE_INDICES.items():
            P_avail, M_avail = self._coils_on_axis_are_available(axis)

            # Different combinations of active coils
            if P_avail and M_avail:
                self._alloc_mat[face_idx["P"]] = MCMConstants.ALLOCATION_MATRIX[face_idx["P"]]
                self._alloc_mat[face_idx["M"]] = MCMConstants.ALLOCATION_MATRIX[face_idx["M"]]

            elif P_avail and not M_avail:
                self._alloc_mat[face_idx["P"]] = 2 * MCMConstants.ALLOCATION_MATRIX[face_idx["P"]]
                self._alloc_mat[face_idx["M"]] = np.zeros(3)

            elif not P_avail and M_avail:
                self._alloc_mat[face_idx["P"]] = np.zeros(3)
                self._alloc_mat[face_idx["M"]] = 2 * MCMConstants.ALLOCATION_MATRIX[face_idx["M"]]

            elif not P_avail and not M_avail:
                self._alloc_mat[face_idx["P"]] = np.zeros(3)
                self._alloc_mat[face_idx["M"]] = np.zeros(3)
