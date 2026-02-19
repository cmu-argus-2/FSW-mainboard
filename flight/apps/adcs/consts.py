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

    # Sensor based Failures
    # Gyro
    GYRO_FAIL = 21
    # Magnetometer
    MAG_FAIL = 31
    # Light Sensor
    SUN_NO_READINGS = 51
    SUN_NOT_ENOUGH_READINGS = 52
    SUN_ECLIPSE = 53

    # Misc
    ZERO_NORM = 61

    # Success Status Constants
    OK = 0

    # Failure Messages
    _FAIL_MESSAGES = {
        GYRO_FAIL: "Gyro failure",
        MAG_FAIL: "Magnetometer failure",
        SUN_NO_READINGS: "No readings",
        SUN_NOT_ENOUGH_READINGS: "Insufficient readings",
        SUN_ECLIPSE: "In eclipse",
        ZERO_NORM: "Zero-normed vector",
        OK: "Success",
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
    SUN_POINTING = 2  # Satellite is generally pointed towards the sun.
    ACS_OFF = 3  # Satellite has pointed to the sun and ACS can be turned off

    SUN_VECTOR_REF = np.array([0.0, 0.0, 1.0])

    # Detumbling
    TUMBLING_TOL = 0.54  # Exit detumbling into stable if ω < 0.54 rad/s (30 deg/s)

    # Detumbling only controllers
    DETUMBLED_TOL_LO = 0.070  # Turn off detumbling  if ω < 0.07 rad/s (4 deg/s)
    DETUMBLED_TOL_HI = 0.087  # Re-enter detumbling if ω > 0.087 rad/s (5 deg/s)

    # STABLE MODE
    STABLE_TOL_LO = 0.26  # Exit into sun_pointing if momentum less than 15 deg from major axis
    STABLE_TOL_HI = 0.34  # Re-enter stable state if momentum more than 20 deg from major axis

    # SUN POINTED MODE
    SUN_POINTED_TOL_LO = 0.176  # Turn ACS off if momentum less than 10 deg from sun vector
    SUN_POINTED_TOL_HI = 0.26  # Re-enter sun_pointed if momentum more than 15 deg from sun vector


class ControllerModes:
    """
    Controller Modes
    """

    BDOT = 0
    BCROSS = 1
    SUN_POINTING = 2


class SunConst:
    """
    Constants associated with sun sensor parameters.
    """

    # map from light sensors to body vector
    LIGHT_SENSOR_NORMALS = [
        [1, 0, 0],
        [-1, 0, 0],
        [0, 1, 0],
        [0, -1, 0],
        [0.7071, 0, 0.7071],
        [0, 0.7071, 0.7071],
        [-0.7071, 0, 0.7071],
        [0, -0.7071, 0.7071],
        [0, 0, -1],
    ]

    LIGHT_X_IDXS = [0, 1, 4, 6]
    LIGHT_Y_IDXS = [2, 3, 5, 7]
    LIGHT_Z_IDXS = [4, 5, 6, 7, 8]

    # Logging only allows for a max value of 65535. Since OPT4003 has a max value of 140k, scale log data down by 3
    LIGHT_SENSOR_LOG_FACTOR = 3


class ControllerConst:
    """
    Constants associated with Controller Behavior
    """

    INERTIA_MAT = np.array(
        [[3.544e-03, -1.8729e-05, -5.2467e-06], [-1.8729e-05, 3.590e-03, 1.9134e-05], [-5.2467e-06, 1.9134e-05, 4.120e-03]]
    )

    # Compute Major axis of inertia
    _eigvals, _eigvecs = np.linalg.eig(INERTIA_MAT)
    _unscaled_axis = _eigvecs[:, np.argmax(_eigvals)]

    INERTIA_MAJOR_DIR = _unscaled_axis / np.linalg.norm(_unscaled_axis)
    inertia_major_dir_abs = np.array([math.fabs(dir_x) for dir_x in INERTIA_MAJOR_DIR])
    if INERTIA_MAJOR_DIR[np.argmax(inertia_major_dir_abs)] < 0:
        INERTIA_MAJOR_DIR = -INERTIA_MAJOR_DIR

    # Dimensions of sensor readings and control input
    READING_DIM = (3,)
    CONTROL_DIM = (3,)

    # Fallback control input
    FALLBACK_CONTROL = np.zeros(CONTROL_DIM)

    # Spin-stabilized Constants
    OMEGA_MAG_TARGET = 0.35  # Target angular velocity (20 deg/s) for spin stabilization
    MOMENTUM_TARGET = np.dot(INERTIA_MAT, INERTIA_MAJOR_DIR * OMEGA_MAG_TARGET)
    MOMENTUM_TARGET_MAG = np.linalg.norm(MOMENTUM_TARGET)
    SPIN_STABILIZING_GAIN = 2.0e07

    # Detumbling Constants
    BDOT_GAIN = 1.0e07
    BCROSS_GAIN = 1.0e07


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
            [-0.5, 0.0, 0.0],
            [0.0, 0.5, 0.0],
            [0.0, -0.5, 0.0],
            [0.0, 0.0, 0.5],
            [0.0, 0.0, -0.5],
        ]
    )
