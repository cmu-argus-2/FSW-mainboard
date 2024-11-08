# Attitude Determination and Control Subsystem (ADCS)
# Magnetic Control Module


# TODO: implement controllers: B-dot, Bcross, Sun pointing
# TODO: implement desired moment allocation to voltages
# ...

# To apply the voltages to the coils, the following function is used:
# SATELLITE.APPLY_MAGNETIC_CONTROL({'XP': 5.0, 'XM': 5.1, 'YP': 4.8, 'YM': 5.0, 'ZP': 4.1, 'ZM': 4.1})


from ulab import numpy as np


class MAGNETIC_COIL_ALLOCATOR():
    _axis_idx  = {
        'X': {'P': 0, 'M': 1},
        'Y': {'P': 2, 'M': 3},
        'Z': {'P': 4, 'M': 5},
    }

    _default_alloc_mat = [
        [0.5, 0.0, 0.0],
        [0.5, 0.0, 0.0],
        [0.0, 0.5, 0.0],
        [0.0, 0.5, 0.0],
        [0.0, 0.0, 0.5],
        [0.0, 0.0, 0.5],
    ]

    def __init__(self) -> None:
        self._alloc_mat = np.array(self._default_alloc_mat)
        self._default_alloc_mat = np.array(self._default_alloc_mat)
        self._n_coil = len(self._alloc_mat)
        # TODO get max voltage from drivers
        #self._Vs_max = get_from_drivers()

    def set_voltages(
        self,
        dipole_moment: np.ndarray,
    ) -> np.ndarray:
        self._update_matrix()
        Vs = self._alloc_mat @ dipole_moment
        Vs_bd = np.clip(Vs, -self._Vs_max, self._Vs_max)
        Vs_ctrl = dict(
            (axis + face, Vs_bd[idx])
            for axis, face_idx in self._axis_idx.items()
            for face, idx in face_idx.items()
        )
        # SATELLITE.APPLY_MAGNETIC_CONTROL(Vs_ctrl)

    def _coils_are_active(
        self,
        axis: str,
    ):
        # TODO get coil status from drivers
        pass

    def _update_matrix(self) -> None:
        for axis, face_idx in self._axis_idx.items():
            coils_are_active = self._coils_are_active(axis)

            # Different combinations of active coils
            if coils_are_active['P'] and coils_are_active['M']:
                self._alloc_mat[face_idx['P']] = self._default_alloc_mat[face_idx['P']]
                self._alloc_mat[face_idx['M']] = self._default_alloc_mat[face_idx['M']]

            elif coils_are_active['P'] and not coils_are_active['M']:
                self._alloc_mat[face_idx['P']] = 2 * self._default_alloc_mat[face_idx['P']]
                self._alloc_mat[face_idx['M']] = np.zeros(3)

            elif not coils_are_active['P'] and coils_are_active['M']:
                self._alloc_mat[face_idx['P']] = np.zeros(3)
                self._alloc_mat[face_idx['M']] = 2 * self._default_alloc_mat[face_idx['M']]

            elif not coils_are_active['P'] and not coils_are_active['M']:
                self._alloc_mat[face_idx['P']] = np.zeros(3)
                self._alloc_mat[face_idx['M']] = np.zeros(3)
