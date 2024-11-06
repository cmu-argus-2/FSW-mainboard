# Attitude Determination and Control Subsystem (ADCS)
# Magnetic Control Module


# TODO: implement controllers: B-dot, Bcross, Sun pointing
# TODO: implement desired moment allocation to voltages
# ...

# To apply the voltages to the coils, the following function is used:
# SATELLITE.APPLY_MAGNETIC_CONTROL({"XP": 5.0, "XM": 5.1, "YP": 4.8, "YM": 5.0, "ZP": 4.1, "ZM": 4.1})


from ulab import numpy as np
from math import pinv


COPPER_RESISTIVITY = 1.724 * 10**-8


MAGNETORQUER_CONFIG = {
        'num_magnetorquers' : 6,
        'orientations': np.column_stack((   # alignment axis in the body frame
            [1,0,0], [0,1,0], [0,0,1], [1,0,0], [0,1,0], [0,0,1]
        )),
        'coils_per_layer': np.array([
            32.0, 32.0, 32.0, 32.0, 32.0, 32.0
        ]),
        'num_layers': np.array([
            2, 2, 2, 2, 2, 2
        ]),
        'trace_width': np.array([
            0.0007317, 0.0007317, 0.0007317, 0.0007317, 0.0007317, 0.0007317
        ]),
        'gap_width': np.array([
            0.00008999, 0.00008999, 0.00008999, 0.00008999, 0.00008999,
            0.00008999
        ]),
        'trace_thickness': np.array([    # 1oz copper - 35um = 1.4 mils
            0.00003556, 0.00003556, 0.00003556, 0.00003556, 0.00003556,
            0.00003556
        ]),
        'pcb_side_max': np.array([
            0.1, 0.1, 0.1, 0.1, 0.1, 0.1
        ]),
        'max_voltage': np.array([
            5.0, 5.0, 5.0, 5.0, 5.0, 5.0
        ]),
        'max_current': np.array([
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0
        ]),
        'max_power': np.array([
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0
        ]),
}


def coil_widths():
    return MAGNETORQUER_CONFIG['trace_width'] \
            + MAGNETORQUER_CONFIG['gap_width']


def coil_lengths():
    return 4 * MAGNETORQUER_CONFIG['coils_per_layer'] \
                * MAGNETORQUER_CONFIG['num_layers'] \
                * (MAGNETORQUER_CONFIG['pcb_side_max'] \
                    - coil_widths() * MAGNETORQUER_CONFIG['coils_per_layer'])


def resistances():
    return COPPER_RESISTIVITY * coil_lengths() \
            / (MAGNETORQUER_CONFIG['trace_width'] \
                * MAGNETORQUER_CONFIG['trace_thickness'])


def coils_per_faces():
    return MAGNETORQUER_CONFIG['coils_per_layer'] \
            * MAGNETORQUER_CONFIG['num_layers']


def A_crosses():
    return (MAGNETORQUER_CONFIG['pcb_side_max'] \
            - MAGNETORQUER_CONFIG['coils_per_layer'] * coil_widths()) ** 2


alloc_mat = pinv(
    MAGNETORQUER_CONFIG['orientations']
        * resistances() / coils_per_faces() /  A_crosses()
)


max_voltages = np.min(np.vstack((
    MAGNETORQUER_CONFIG['max_voltage'],
    resistances() * MAGNETORQUER_CONFIG['max_current'],
    np.sqrt(resistances() * MAGNETORQUER_CONFIG['max_power'])), axis=1
))


def allocate_voltages(
    dipole_moment: np.ndarray,
) -> np.ndarray:
    voltages = alloc_mat @ dipole_moment
    return np.clip(voltages, -max_voltages, max_voltages)
