"""
Constants used in ADCS apps.

Author(s): Derek Fan
"""

import math
import os
import struct

from core.satellite_config import adcs_config as CONFIG
from ulab import numpy as np

_CTR_MODE_DIR = "/sd/config/"
_CTRL_MODE_PATH = _CTR_MODE_DIR + "controller_mode.bin"
_CTRL_CONSTS_PATH = _CTR_MODE_DIR + "controller_consts.bin"
_MODE_TOLS_PATH = _CTR_MODE_DIR + "mode_tols.bin"


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

    # # Failure Messages
    # _FAIL_MESSAGES = {
    #     GYRO_FAIL: "Gyro failure",
    #     MAG_FAIL: "Magnetometer failure",
    #     SUN_NO_READINGS: "No readings",
    #     SUN_NOT_ENOUGH_READINGS: "Insufficient readings",
    #     SUN_ECLIPSE: "In eclipse",
    #     ZERO_NORM: "Zero-normed vector",
    #     OK: "Success",
    # }

    # @classmethod
    # def get_fail_message(cls, status):
    #     return cls._FAIL_MESSAGES.get(status, "Unknown error code")


class Modes:
    """
    Modes and their corresponding thresholds
    """

    TUMBLING = 0  # Satellite is spinning outside the "stable" bounds.
    STABLE = 1  # Satellite is spinning inside the "stable" bounds.
    SUN_POINTING = 2  # Satellite is generally pointed towards the sun.
    ACS_OFF = 3  # Satellite has pointed to the sun and ACS can be turned off
    VF_TUMBLING = 4  # Satellite is tumbling too fast for the ACS to work

    # Detumbling
    VF_TUMBLING_TOL_BDOT = 2.62  # 1.75  # Enter VF tumbling if ω > 1.75 rad/s (100 deg/s)
    VF_TUMBLING_TOL = 5.24  # 3.49  # Enter VF tumbling if ω > 3.49 rad/s (200 deg/s)
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

    _loaded = False

    @classmethod
    def load(cls):
        if cls._loaded:
            return
        try:
            with open(_MODE_TOLS_PATH, "rb") as f:
                vals = struct.unpack("5f", f.read(struct.calcsize("5f")))
            cls.VF_TUMBLING_TOL_BDOT = vals[0]
            cls.VF_TUMBLING_TOL = vals[1]
            cls.TUMBLING_TOL = vals[2]
            cls.DETUMBLED_TOL_LO = vals[3]
            cls.DETUMBLED_TOL_HI = vals[4]
        except Exception:
            pass
        cls._loaded = True

    @classmethod
    def _save(cls):
        if not cls._loaded:
            return
        try:
            with open(_MODE_TOLS_PATH, "wb") as f:
                f.write(
                    struct.pack(
                        "5f",
                        cls.VF_TUMBLING_TOL_BDOT,
                        cls.VF_TUMBLING_TOL,
                        cls.TUMBLING_TOL,
                        cls.DETUMBLED_TOL_LO,
                        cls.DETUMBLED_TOL_HI,
                    )
                )
            os.sync()
        except Exception:
            pass

    @classmethod
    def update_vf_tumbling_tols(cls, bdot, vf):
        cls.VF_TUMBLING_TOL_BDOT = bdot
        cls.VF_TUMBLING_TOL = vf
        cls._save()

    @classmethod
    def update_detumbling_tols(cls, tumbling, lo, hi):
        cls.TUMBLING_TOL = tumbling
        cls.DETUMBLED_TOL_LO = lo
        cls.DETUMBLED_TOL_HI = hi
        cls._save()


class ControllerModes:
    """
    Controller Modes
    """

    BDOT = 0
    BCROSS = 1
    SUN_POINTING = 2

    current_mode = CONFIG.CONTROLLER_MODE
    _loaded = False

    @classmethod
    def load(cls):
        if cls._loaded:
            return
        try:
            with open(_CTRL_MODE_PATH, "rb") as f:
                mode = struct.unpack("B", f.read(1))[0]
                if mode in (cls.BDOT, cls.BCROSS, cls.SUN_POINTING):
                    cls.current_mode = mode
                    cls._loaded = True
                    return
        except Exception:
            pass
        try:
            os.remove(_CTRL_MODE_PATH)
        except Exception:
            pass
        try:
            os.mkdir(_CTR_MODE_DIR)
        except Exception:
            pass
        try:
            with open(_CTRL_MODE_PATH, "wb") as f:
                f.write(struct.pack("B", CONFIG.CONTROLLER_MODE))
            os.sync()
            cls._loaded = True
        except Exception:
            pass

    @classmethod
    def update_mode(cls, new_mode):
        if new_mode in [cls.BDOT, cls.BCROSS, cls.SUN_POINTING]:
            cls.current_mode = new_mode
            try:
                with open(_CTRL_MODE_PATH, "wb") as f:
                    f.write(struct.pack("B", new_mode))
                os.sync()
            except Exception:
                pass
            return True
        return False


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
        [0, -0.7071, 0.7071],
        [-0.7071, 0, 0.7071],
        [0, 0.7071, 0.7071],
        [0, 0, -1],
    ]

    LIGHT_X_IDXS = [0, 1, 4, 6]
    LIGHT_Y_IDXS = [2, 3, 5, 7]
    LIGHT_Z_IDXS = [4, 5, 6, 7, 8]

    # Logging only allows for a max value of 65535. Since OPT4003 has a max value of 140k, scale log data down by 3
    LIGHT_SENSOR_LOG_FACTOR = 1 / 3


class ControllerConst:
    """
    Constants associated with Controller Behavior
    """

    INERTIA_MAT = np.array(
        [[3.544e-03, -1.8729e-05, -5.2467e-06], [-1.8729e-05, 3.590e-03, 1.9134e-05], [-5.2467e-06, 1.9134e-05, 4.120e-03]]
    )

    # Hardcoded Inertia Major Dir
    INERTIA_MAJOR_DIR = np.array([-0.01027212, 0.03638753, 0.99928496])

    # Dimensions of sensor readings and control input
    READING_DIM = (3,)

    # Fallback control input
    FALLBACK_CONTROL = np.zeros(3)

    # Spin-stabilized Constants
    OMEGA_MAG_TARGET = 0.35  # Target angular velocity (20 deg/s) for spin stabilization
    MOMENTUM_TARGET = np.dot(INERTIA_MAT, INERTIA_MAJOR_DIR * OMEGA_MAG_TARGET)
    MOMENTUM_TARGET_MAG = np.linalg.norm(MOMENTUM_TARGET)
    SPIN_STABILIZING_GAIN = 2.0e07

    # Detumbling Constants
    DETUMB_GAIN = 1.0e05

    _loaded = False

    @classmethod
    def load(cls):
        if cls._loaded:
            return
        try:
            with open(_CTRL_CONSTS_PATH, "rb") as f:
                vals = struct.unpack("9f", f.read(struct.calcsize("9f")))
            cls.update_gains(vals[0], vals[1])
            cls.update_omega_target(vals[2])
            cls.update_inertia(vals[3], vals[4], vals[5], vals[6], vals[7], vals[8])
        except Exception:
            pass
        cls._loaded = True

    @classmethod
    def _save(cls):
        if not cls._loaded:
            return
        try:
            m = cls.INERTIA_MAT
            with open(_CTRL_CONSTS_PATH, "wb") as f:
                f.write(
                    struct.pack(
                        "9f",
                        cls.SPIN_STABILIZING_GAIN,
                        cls.DETUMB_GAIN,
                        cls.OMEGA_MAG_TARGET,
                        m[0][0],
                        m[0][1],
                        m[0][2],
                        m[1][1],
                        m[1][2],
                        m[2][2],
                    )
                )
            os.sync()
        except Exception:
            pass

    @classmethod
    def update_gains(cls, spin_gain, detumb_gain):
        cls.SPIN_STABILIZING_GAIN = spin_gain
        cls.DETUMB_GAIN = detumb_gain
        cls._save()

    @classmethod
    def update_omega_target(cls, omega_mag_target):
        cls.OMEGA_MAG_TARGET = omega_mag_target
        cls.MOMENTUM_TARGET = np.dot(cls.INERTIA_MAT, cls.INERTIA_MAJOR_DIR * omega_mag_target)
        cls.MOMENTUM_TARGET_MAG = np.linalg.norm(cls.MOMENTUM_TARGET)
        cls._save()

    @classmethod
    def update_inertia(cls, ixx, ixy, ixz, iyy, iyz, izz):
        cls.INERTIA_MAT = np.array([[ixx, ixy, ixz], [ixy, iyy, iyz], [ixz, iyz, izz]])

        # Compute Major axis of inertia
        _eigvals, _eigvecs = np.linalg.eig(cls.INERTIA_MAT)
        _unscaled_axis = _eigvecs[:, np.argmax(_eigvals)]
        cls.INERTIA_MAJOR_DIR = _unscaled_axis / np.linalg.norm(_unscaled_axis)
        inertia_major_dir_abs = np.array([math.fabs(dir_x) for dir_x in cls.INERTIA_MAJOR_DIR])
        if cls.INERTIA_MAJOR_DIR[np.argmax(inertia_major_dir_abs)] < 0:
            cls.INERTIA_MAJOR_DIR = -cls.INERTIA_MAJOR_DIR

        cls.MOMENTUM_TARGET = np.dot(cls.INERTIA_MAT, cls.INERTIA_MAJOR_DIR * cls.OMEGA_MAG_TARGET)
        cls.MOMENTUM_TARGET_MAG = np.linalg.norm(cls.MOMENTUM_TARGET)
        cls._save()


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
