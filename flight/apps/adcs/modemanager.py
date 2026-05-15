"""
    MODE DETERMINATION
"""
from apps.adcs.consts import ControllerConst, ControllerModes, Modes, StatusConst
from ulab import numpy as np


def update_mode(current_mode, ctr_mode, gyro_status, omega, sun_status=None, sun_pos_body=None) -> int:
    """
    - Returns the current mode of the ADCS
    """
    # Fail-safe STABLE mode if IMU fails
    if gyro_status != StatusConst.OK:
        return Modes.STABLE

    # Tumbling state logic - common to all controllers
    # Used to set FSW state machine to DETUMBLING
    omega_norm = np.linalg.norm(omega)

    if current_mode == Modes.TUMBLING:
        if omega_norm <= Modes.TUMBLING_TOL:
            return Modes.STABLE
        return Modes.TUMBLING
    if omega_norm >= Modes.TUMBLING_TOL:
        return Modes.TUMBLING

    # # Controller specific mode logic
    if ctr_mode != ControllerModes.SUN_POINTING:
        # # Detumbling mode - B-cross or B-dot controller
        if current_mode == Modes.STABLE:
            if omega_norm < Modes.DETUMBLED_TOL_LO:
                return Modes.ACS_OFF
            return Modes.STABLE

        # if current_mode == Modes.ACS_OFF: -> implicit
        if omega_norm >= Modes.DETUMBLED_TOL_HI:
            return Modes.STABLE
        return Modes.ACS_OFF
    # # Sun-pointing mode
    h = np.dot(ControllerConst.INERTIA_MAT, omega)
    momentum_error = np.linalg.norm(ControllerConst.INERTIA_MAJOR_DIR - (h / ControllerConst.MOMENTUM_TARGET_MAG))

    if current_mode == Modes.STABLE:
        if momentum_error <= Modes.STABLE_TOL_LO and sun_status == StatusConst.OK:
            return Modes.SUN_POINTING
        return Modes.STABLE

    if sun_status != StatusConst.OK:
        return current_mode
    h_norm = np.linalg.norm(h)
    if h_norm == 0:
        return Modes.SUN_POINTING
    sun_error = np.linalg.norm(sun_pos_body - h / h_norm)

    if current_mode == Modes.SUN_POINTING:
        if momentum_error >= Modes.STABLE_TOL_LO:
            return Modes.STABLE
        # implicit sun_status == StatusConst.OK
        if sun_error <= Modes.SUN_POINTED_TOL_LO:
            return Modes.ACS_OFF

        return Modes.SUN_POINTING

    # if current_mode == Modes.ACS_OFF: -> implicit
    if momentum_error >= Modes.STABLE_TOL_HI:
        return Modes.STABLE
    # implicit sun_status == StatusConst.OK
    if sun_error >= Modes.SUN_POINTED_TOL_HI:
        return Modes.SUN_POINTING
    return Modes.ACS_OFF
