from ulab import numpy as np


class ModeConst:
    """
    Constants used for determining ADCS mode.
    """

    STABLE_TOLERANCE = 0.05  # "stable" if ang vel < 0.05 rad/s = 2.86 deg/s.
    SUN_POINTED_TOLERANCE = 0.09  # "sun-pointed" if att err < 0.09 rad = 5 deg.
    SUN_VECTOR_REFERENCE = np.array([0.0, 0.0, 1.0])


class PhysicalConst:
    """
    Constants associated with physical satellite bus parameters.
    """

    INERTIA_MAT = np.array(
        [
            [0.001796, 0.0, 0.000716],
            [0.0, 0.002081, 0.0],
            [0.000716, 0.0, 0.002232],
        ]
    )


class MagnetorquerConst:
    """
    Constants associated with physical magnetorquer parameters.
    Assume all magnetorquers are identical.
    """

    V_MAX = 5.0

    NUM_LAYERS = 2.0
    COILS_PER_LAYER = 32.0
    TRACE_THICKNESS = 3.556e-5
    TRACE_WIDTH = 0.0007317
    GAP_WIDTH = 8.999e-5

    PCB_SIDE_MAX = 0.1
    COPPER_RESIST = 1.724e-8

    COIL_WIDTH = TRACE_WIDTH + GAP_WIDTH
    COIL_LENGTH = 4 * (PCB_SIDE_MAX - COILS_PER_LAYER * COIL_WIDTH) * COILS_PER_LAYER * NUM_LAYERS

    A_CROSS = (PCB_SIDE_MAX - COILS_PER_LAYER * COIL_WIDTH) ** 2
    RESIST = COPPER_RESIST * COIL_LENGTH / (TRACE_WIDTH * TRACE_THICKNESS)
    V_CONVERT = RESIST / (COILS_PER_LAYER * NUM_LAYERS * A_CROSS)


class MCMConst:
    """
    Constants used for magnetorquer control and allocation.
    """

    AXIS_FACE_INDICES = {
        "X": {"P": 0, "M": 1},
        "Y": {"P": 2, "M": 3},
        "Z": {"P": 4, "M": 5},
    }

    ALLOC_MAT = np.array(
        [
            [0.5, 0.0, 0.0],
            [0.5, 0.0, 0.0],
            [0.0, 0.5, 0.0],
            [0.0, 0.5, 0.0],
            [0.0, 0.0, 0.5],
            [0.0, 0.0, 0.5],
        ]
    )

    PD_GAINS = np.array(
        [
            [0.7071, 0.0, 0.0, 0.0028, 0.0, 0.0],
            [0.0, 0.7071, 0.0, 0.0, 0.0028, 0.0],
            [0.0, 0.0, 0.7071, 0.0, 0.0, 0.0028],
        ]
    )

    BCROSS_GAIN = 0.0028
    ANG_VEL_NORM_TARGET = 0.175
    ANG_VEL_NORM_THRESHOLD = 0.262
