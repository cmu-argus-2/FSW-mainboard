# Attitude Determination and Control Subsystem (ADCS)
# Magnetic Control Module


# TODO: implement controllers: B-dot, Bcross, Sun pointing
# TODO: implement desired moment allocation to voltages
# ...

# To apply the voltages to the coils, the following function is used:
# SATELLITE.APPLY_MAGNETIC_CONTROL({'XP': 5.0, 'XM': 5.1, 'YP': 4.8, 'YM': 5.0, 'ZP': 4.1, 'ZM': 4.1})

import copy
from typing import Tuple

from ulab import numpy as np

from hal.configuration import SATELLITE


class BCrossController():
    _k = 1.0

    @classmethod
    def get_dipole_moment_command(
        self,
        magnetic_field: np.ndarray,
        angular_velocity: np.ndarray,
        angular_velocity_ref: np.ndarray,
    ) -> np.ndarray:
        """
        B-cross law: https://arc.aiaa.org/doi/epdf/10.2514/1.53074
        """
        unit_field = magnetic_field / np.linalg.norm(magnetic_field)
        return -self._k * np.cross(unit_field, angular_velocity - angular_velocity_ref)


class MagneticCoilAllocator():
    _Vs_ctrl = {
        'XP': 0.0, 'XM': 0.0,
        'YP': 0.0, 'YM': 0.0,
        'zP': 0.0, 'zM': 0.0,
    }

    _axis_idx  = {
        'X': {'P': 0, 'M': 1},
        'Y': {'P': 2, 'M': 3},
        'Z': {'P': 4, 'M': 5},
    }

    _default_alloc_mat = np.array([
        [0.5, 0.0, 0.0],
        [0.5, 0.0, 0.0],
        [0.0, 0.5, 0.0],
        [0.0, 0.5, 0.0],
        [0.0, 0.0, 0.5],
        [0.0, 0.0, 0.5],
    ])

    _alloc_mat = copy.deepcopy(_default_alloc_mat)

    _Vs_max = [5.0, 5.0, 5.0, 5.0, 5.0, 5.0]

    _sat = SATELLITE

    _n_coil = len(_alloc_mat)


    @classmethod
    def set_voltages(
        self,
        dipole_moment: np.ndarray,
    ) -> None:
        self._update_matrix()
        Vs = self._alloc_mat @ dipole_moment
        Vs_bd = np.clip(Vs, -self._Vs_max, self._Vs_max)
        for axis, face_idx in self._axis_idx.items():
            self._Vs_ctrl[axis + 'P'] = Vs_bd[face_idx['P']]
            self._Vs_ctrl[axis + 'M'] = Vs_bd[face_idx['M']]
        self._sat.APPLY_MAGNETIC_CONTROL(self._Vs_ctrl)

    @classmethod
    def _coils_on_axis_are_available(
        self,
        axis: str,
    ) -> Tuple[bool, bool]:
        P_avail = self._sat.TORQUE_DRIVERS_AVAILABLE(axis + 'P')
        M_avail = self._sat.TORQUE_DRIVERS_AVAILABLE(axis + 'M')
        return (P_avail, M_avail)

    @classmethod
    def _update_matrix(self) -> None:
        for axis, face_idx in self._axis_idx.items():
            P_avail, M_avail = self._coils_on_axis_are_available(axis)

            # Different combinations of active coils
            if P_avail and M_avail:
                self._alloc_mat[face_idx['P']] = self._default_alloc_mat[face_idx['P']]
                self._alloc_mat[face_idx['M']] = self._default_alloc_mat[face_idx['M']]

            elif P_avail and not M_avail:
                self._alloc_mat[face_idx['P']] = 2 * self._default_alloc_mat[face_idx['P']]
                self._alloc_mat[face_idx['M']] = np.zeros(3)

            elif not P_avail and M_avail:
                self._alloc_mat[face_idx['P']] = np.zeros(3)
                self._alloc_mat[face_idx['M']] = 2 * self._default_alloc_mat[face_idx['M']]

            elif not P_avail and not M_avail:
                self._alloc_mat[face_idx['P']] = np.zeros(3)
                self._alloc_mat[face_idx['M']] = np.zeros(3)
