"""
Constants used in ADCS apps.

Author(s): Derek Fan
"""


from core.satellite_config import adcs_config as CONFIG
from ulab import numpy as np

_CTR_MODE_DIR = "/sd/config/"
_CTRL_MODE_PATH = _CTR_MODE_DIR + "controller_mode.bin"


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
    VF_TUMBLING_TOL_BDOT = 2.62  # Enter VF tumbling if ω > 2.62 rad/s (150 deg/s)
    VF_TUMBLING_TOL = 3.05  # Enter VF tumbling if ω > 3.05 rad/s (175 deg/s)
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

    current_mode = CONFIG.CONTROLLER_MODE
    _loaded = False

    @classmethod
    def load(cls):
        if cls._loaded:
            return
        import os
        import struct
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
                import os
                import struct
                with open(_CTRL_MODE_PATH, "wb") as f:
                    f.write(struct.pack("B", new_mode))
                os.sync()
            except Exception:
                pass
            return True
        return False


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
