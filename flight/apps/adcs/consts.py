"""
Constants used in ADCS apps.

Author(s): Derek Fan
"""

from ulab import numpy as np


class Modes:
    """
    Modes and their corresponding thresholds
    """

    TUMBLING = 0  # Satellite is spinning outside the "stable" bounds.
    STABLE = 1  # Satellite is spinning inside the "stable" bounds.
    SUN_POINTED = 2  # Satellite is generally pointed towards the sun.

    SUN_VECTOR_REF = np.array([0.0, 0.0, 1.0])
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


class MCMConst:
    """
    Constants used for magnetorquer control and allocation.
    """

    N_MCM = 6
    MCM_FACES = ["XP", "XM", "YP", "YM", "ZP", "ZM"]
    MCM_INDICES = [0, 1, 2, 3, 4, 5]

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
