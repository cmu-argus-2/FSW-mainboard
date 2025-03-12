"""
Constants used in ADCS apps.

Author(s): Derek Fan
"""

import math

from ulab import numpy as np


class StatusConst:
    """
    Status codes used in ADCS apps.
    """

    """
        Failure Status Constants
    """

    # Algorithm Failures
    MEKF_INIT_FAIL = -1
    OPROP_INIT_FAIL = -2
    TRIAD_FAIL = -3
    POS_UPDATE_FAIL = -4
    SUN_UPDATE_FAIL = -5
    MAG_UPDATE_FAIL = -6
    EKF_UPDATE_FAIL = -7
    TRUE_SUN_MAP_FAIL = -8
    TRUE_MAG_MAP_FAIL = -9

    # Sensor based Failures
    # Gyro
    GYRO_FAIL = -11
    # Magnetometer
    MAG_FAIL = -21
    # GPS
    GPS_FAIL = -31
    # Light Sensor
    SUN_NO_READINGS = -41
    SUN_NOT_ENOUGH_READINGS = -42
    SUN_ECLIPSE = -43

    # Misc
    ZERO_NORM = -51

    # Success Status Constants
    OK = 1

    # Failure Messages
    _FAIL_MESSAGES = {
        MEKF_INIT_FAIL: "MEKF init failure",
        OPROP_INIT_FAIL: "Orbit Prop Init failure",
        TRIAD_FAIL: "TRIAD failure",
        POS_UPDATE_FAIL: "Position update failure",
        SUN_UPDATE_FAIL: "Sun update failure",
        MAG_UPDATE_FAIL: "Mag update failure",
        EKF_UPDATE_FAIL: "Singular Matrix",
        TRUE_SUN_MAP_FAIL: "Invalid true sunpos",
        TRUE_MAG_MAP_FAIL: "Invalid true mag",
        GYRO_FAIL: "Gyro failure",
        MAG_FAIL: "Magnetometer failure",
        GPS_FAIL: "GPS failure",
        SUN_NO_READINGS: "No readings",
        SUN_NOT_ENOUGH_READINGS: "Insufficient readings",
        SUN_ECLIPSE: "In eclipse",
        ZERO_NORM: "Zero-normed vector",
    }

    @classmethod
    def get_fail_message(cls, status):
        return cls._FAIL_MESSAGES.get(status, "Unknown error code")


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
    inertia_major_dir_abs = np.array([math.fabs(dir_x) for dir_x in INERTIA_MAJOR_DIR])
    if INERTIA_MAJOR_DIR[np.argmax(inertia_major_dir_abs)] < 0:
        INERTIA_MAJOR_DIR = -INERTIA_MAJOR_DIR


class ControllerConst:
    """
    Constants associated with Controller Behavior
    """

    # Dimensions of sensor readings and control input
    READING_DIM = (3,)
    CONTROL_DIM = (3,)

    # Fallback control input
    FALLBACK_CONTROL = np.zeros(CONTROL_DIM)

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
