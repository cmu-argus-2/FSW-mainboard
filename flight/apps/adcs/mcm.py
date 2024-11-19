# Attitude Determination and Control Subsystem (ADCS)
# Magnetic Control Module


# TODO: implement controllers: B-dot, Bcross, Sun pointing
# TODO: implement desired moment allocation to voltages
# ...

# To apply the voltages to the coils, the following function is used:
# SATELLITE.APPLY_MAGNETIC_CONTROL({'XP': 5.0, 'XM': 5.1, 'YP': 4.8, 'YM': 5.0, 'ZP': 4.1, 'ZM': 4.1})

import copy
from typing import Tuple

from hal.configuration import SATELLITE
from ulab import numpy as np


def skew(v: np.ndarray):
    return np.array(
        [
            [0.0, -v[2], v[1]],
            [v[2], 0.0, -v[0]],
            [-v[1], v[0], 0.0],
        ]
    )


"""
Template for magnetic dipole moment control.
"""


class MagnetorquerController:
    def get_dipole_moment_command():
        raise NotImplementedError()


"""
Implemented control laws.
"""


class BCrossController(MagnetorquerController):
    _k = 1.0

    @classmethod
    def get_dipole_moment_command(
        self,
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
        return -self._k * np.cross(unit_field, ang_vel_err)


class PDSunPointingController(MagnetorquerController):
    _PD_gains = np.array(
        [
            [0.7071, 0.0, 0.0, 0.0028, 0.0, 0.0],
            [0.0, 0.7071, 0.0, 0.0, 0.0028, 0.0],
            [0.0, 0.0, 0.7071, 0.0, 0.0, 0.0028],
        ]
    )

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
        return Bhat_pinv @ self._PD_gains @ att_angvel_err


"""
High-level controller and allocation managers.
"""


class ControllerHandler(MagnetorquerController):
    _J = np.array(
        [
            [0.001796, 0.0, 0.000716],
            [0.0, 0.002081, 0.0],
            [0.000716, 0.0, 0.002232],
        ]
    )

    _ang_vel_norm_target = 0.175  # rad/s

    _ang_vel_norm_threshold = 0.262  # rad/s

    @classmethod
    def _init_spin_axis(self) -> np.ndarray:
        eigvecs, eigvals = np.linalg.eig(self._J)
        spin_axis = eigvecs[:, np.argmax(eigvals)]
        if spin_axis[np.argmax(np.abs(spin_axis))] < 0:
            spin_axis = -spin_axis
        return spin_axis

    spin_axis = _init_spin_axis()

    ang_vel_reference = spin_axis * _ang_vel_norm_target

    _h_norm_target = np.linalg.norm(_J @ ang_vel_reference)
    """
    @classmethod
    def _get_reused_values(
        self,
        magnetic_field: np.ndarray,
        angular_velocity: np.ndarray,
    ) -> Tuple[np.ndarray, float]:
        h = self._J @ angular_velocity
        b_norm = np.linalg.norm(magnetic_field)
        return h, b_norm
    """

    @classmethod
    def is_spin_stable(
        self,
        angular_momentum: np.ndarray,
    ) -> bool:
        spin_err = np.linalg.norm(self.spin_axis - (angular_momentum / self._h_norm_target))
        return spin_err < self._ang_vel_norm_threshold

    @classmethod
    def is_sun_pointing(
        self,
        sun_vector: np.ndarray,
        angular_momentum: np.ndarray,
    ) -> bool:
        h_norm = np.linalg.norm(angular_momentum)
        pointing_err = np.linalg.norm(sun_vector - (angular_momentum / h_norm))
        return pointing_err < self._ang_vel_norm_target

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


class MagneticCoilAllocator:
    _Vs_ctrl = {
        "XP": 0.0,
        "XM": 0.0,
        "YP": 0.0,
        "YM": 0.0,
        "zP": 0.0,
        "zM": 0.0,
    }

    _axis_idx = {
        "X": {"P": 0, "M": 1},
        "Y": {"P": 2, "M": 3},
        "Z": {"P": 4, "M": 5},
    }

    _default_alloc_mat = np.array(
        [
            [0.5, 0.0, 0.0],
            [0.5, 0.0, 0.0],
            [0.0, 0.5, 0.0],
            [0.0, 0.5, 0.0],
            [0.0, 0.0, 0.5],
            [0.0, 0.0, 0.5],
        ]
    )

    _alloc_mat = copy.deepcopy(_default_alloc_mat)

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
        for axis, face_idx in self._axis_idx.items():
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
        return (P_avail, M_avail)

    @classmethod
    def _update_matrix(self) -> None:
        for axis, face_idx in self._axis_idx.items():
            P_avail, M_avail = self._coils_on_axis_are_available(axis)

            # Different combinations of active coils
            if P_avail and M_avail:
                self._alloc_mat[face_idx["P"]] = self._default_alloc_mat[face_idx["P"]]
                self._alloc_mat[face_idx["M"]] = self._default_alloc_mat[face_idx["M"]]

            elif P_avail and not M_avail:
                self._alloc_mat[face_idx["P"]] = 2 * self._default_alloc_mat[face_idx["P"]]
                self._alloc_mat[face_idx["M"]] = np.zeros(3)

            elif not P_avail and M_avail:
                self._alloc_mat[face_idx["P"]] = np.zeros(3)
                self._alloc_mat[face_idx["M"]] = 2 * self._default_alloc_mat[face_idx["M"]]

            elif not P_avail and not M_avail:
                self._alloc_mat[face_idx["P"]] = np.zeros(3)
                self._alloc_mat[face_idx["M"]] = np.zeros(3)
