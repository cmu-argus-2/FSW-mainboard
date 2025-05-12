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
    MEKF_INIT_FAIL = 1
    MEKF_INIT_FORCE = 2
    OPROP_INIT_FAIL = 3
    TRIAD_FAIL = 4
    POS_UPDATE_FAIL = 5
    SUN_UPDATE_FAIL = 6
    MAG_UPDATE_FAIL = 7
    EKF_UPDATE_FAIL = 8
    TRUE_SUN_MAP_FAIL = 9
    TRUE_MAG_MAP_FAIL = 10

    # Sensor based Failures
    # Gyro
    GYRO_FAIL = 21
    # Magnetometer
    MAG_FAIL = 31
    # GPS
    GPS_FAIL = 41
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
        MEKF_INIT_FAIL: "MEKF init failure",
        MEKF_INIT_FORCE: "Force initializing MEKF",
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
    SUN_POINTED = 2  # Satellite is generally pointed towards the sun.
    ACS_OFF = 3  # Satellite has pointed to the sun and ACS can be turned off

    SUN_VECTOR_REF = np.array([0.0, 0.0, 1.0])

    # Detumbling
    TUMBLING_LO = 0.03  # Exit detumbling into stable if ω < 0.03 rad/s (2 deg/s)
    TUMBLING_HI = 0.05

    # Re-enter detumbling if ω > 0.09 rad/s (5 deg/s)

    # STABLE MODE
    STABLE_TOL_LO = 0.01  # Exit into sun_pointing if angular momentum error norm < 0.01
    STABLE_TOL_HI = 0.03  # Re-enter stable state if angular momentum error norm > 0.03

    SUN_POINTED_TOL = 0.05  # "sun-pointed" if att err < 0.09 rad = 5 deg.


class PhysicalConst:
    """
    Constants associated with physical satellite bus parameters.
    """

    INERTIA_MAT = np.array(
        [[3.544e-03, -1.8729e-05, -5.2467e-06], [-1.8729e-05, 3.590e-03, 1.9134e-05], [-5.2467e-06, 1.9134e-05, 4.120e-03]]
    )
    INERTIA_DET = np.linalg.det(INERTIA_MAT)

    # Compute Major axis of inertia
    _eigvals, _eigvecs = np.linalg.eig(INERTIA_MAT)
    _unscaled_axis = _eigvecs[:, np.argmax(_eigvals)]

    INERTIA_MAJOR_DIR = _unscaled_axis / np.linalg.norm(_unscaled_axis)
    inertia_major_dir_abs = np.array([math.fabs(dir_x) for dir_x in INERTIA_MAJOR_DIR])
    if INERTIA_MAJOR_DIR[np.argmax(inertia_major_dir_abs)] < 0:
        INERTIA_MAJOR_DIR = -INERTIA_MAJOR_DIR

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

    # Dimensions of sensor readings and control input
    READING_DIM = (3,)
    CONTROL_DIM = (3,)

    # Fallback control input
    FALLBACK_CONTROL = np.zeros(CONTROL_DIM)

    # Spin-stabilized Constants
    OMEGA_MAG_TARGET = Modes.TUMBLING_LO  # Target angular velocity along major axis -> Required ω for stable confn
    MOMENTUM_TARGET = np.dot(PhysicalConst.INERTIA_MAT, PhysicalConst.INERTIA_MAJOR_DIR * OMEGA_MAG_TARGET)
    SPIN_STABILIZING_GAIN = 2.0e07

    # Sun Pointing Constants

    # Tolerances
    OMEGA_TOLERANCE = 0.02  # rad/s (~1.2 deg/s)


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
