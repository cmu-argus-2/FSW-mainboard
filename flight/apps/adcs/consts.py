from ulab import numpy as np


class ModeConstants:
    """
    Constants used for determining ADCS mode.
    """

    STABLE_TOLERANCE = 0.05  # "stable" if ang vel < 0.05 rad/s = 2.86 deg/s.
    SUN_POINTED_TOLERANCE = 0.09  # "sun-pointed" if att err < 0.09 rad = 5 deg.
    SUN_VECTOR_REFERENCE = np.array([0.0, 0.0, 1.0])


class PhysicalConstants:
    """
    Constants associated with physical parameters.
    """

    INERTIA_TENSOR = np.array(
        [
            [0.001796, 0.0, 0.000716],
            [0.0, 0.002081, 0.0],
            [0.000716, 0.0, 0.002232],
        ]
    )


class MCMConstants:
    """
    Constants used for magnetic coil control and allocation.
    """

    AXIS_FACE_INDICES = {
        "X": {"P": 0, "M": 1},
        "Y": {"P": 2, "M": 3},
        "Z": {"P": 4, "M": 5},
    }

    ALLOCATION_MATRIX = np.array(
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

    BCROSS_GAIN = 1.0
    ANG_VEL_NORM_TARGET = 0.175
    ANG_VEL_NORM_THRESHOLD = 0.262
