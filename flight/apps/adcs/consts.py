"""
Constants used in ADCS apps.

Author(s): Derek Fan
"""

from ulab import numpy as np


class ModeConst:
    """
    Constants used for determining ADCS mode.
    """

    SUN_VECTOR_REF = np.array([0.0, 0.0, 1.0])
    EKF_INIT_TOL = 0.3  # MEKF can be initialized if ang vel < 0.2 rad/s = 11 deg/s
    STABLE_TOL = 0.14  # 0.05  # "stable" if ang vel < 0.05 rad/s = 2.86 deg/s.
    SUN_POINTED_TOL = 0.1  # "sun-pointed" if att err < 0.09 rad = 5 deg.


class PhysicalConst:
    """
    Constants associated with physical satellite bus parameters.
    """

    INERTIA_MAT = np.array(
        [
            [0.0033, 0.0, 0.0],
            [0.0, 0.0033, 0.0],
            [0.0, 0.0, 0.0066],
        ]
    )

    # Compute Major axis of inertia
    _eigvals, _eigvecs = np.linalg.eig(INERTIA_MAT)
    _unscaled_axis = _eigvecs[:, np.argmax(_eigvals)]

    INERTIA_MAJOR_DIR = _unscaled_axis / np.linalg.norm(_unscaled_axis)
    if INERTIA_MAJOR_DIR[np.argmax(np.abs(INERTIA_MAJOR_DIR))] < 0:
        INERTIA_MAJOR_DIR = -INERTIA_MAJOR_DIR


class ControllerConst:
    """
    Constants associated with Controller Behavior
    """

    # Spin-stabilized Constants
    OMEGA_MAG_TARGET = 0.1125  # Target angular velocity along major axis
    MOMENTUM_TARGET = np.linalg.norm(np.dot(PhysicalConst.INERTIA_MAT, PhysicalConst.INERTIA_MAJOR_DIR * OMEGA_MAG_TARGET))
    SPIN_STABILIZING_GAIN = 1.0e06

    # Sun Pointing Constants


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

    REF_FACTOR = 0.75
    SPIN_ERROR_TOL = 0.15
    POINTING_ERROR_TOL = 0.01
    SPIN_STABILIZING_GAIN = 1.0e06
    # SUN_POINTING_GAIN = 5.0e05

    """ AXIS_FACE_INDICES = {
        "X": {"P": 0, "M": 1},
        "Y": {"P": 2, "M": 3},
        "Z": {"P": 4, "M": 5},
    } """

    N_MCM = 6
    MCM_FACES = ["XP", "XM", "YP", "YM", "ZP", "ZM"]
    MCM_INDICES = [0, 1, 2, 3, 4, 5]
    AXIS_FACE_INDEX_MAP = {"XP": 0, "XM": 1, "YP": 2, "YM": 3, "ZP": 4, "ZM": 5}

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
