"""
    MODE DETERMINATION
"""
import apps.adcs.sensors as sensors
from apps.adcs.consts import ControllerConst, ControllerModes, Modes, StatusConst
from ulab import numpy as np


def update_mode(current_mode, ctr_mode) -> int:
    """
    - Returns the current mode of the ADCS
    """
    if ctr_mode in [ControllerModes.BCROSS, ControllerModes.BDOT]:
        return update_mode_detumbling(current_mode)
    if ctr_mode == ControllerModes.SUN_POINTING:
        return update_mode_sun_pointing(current_mode)
    raise ValueError(f"Invalid Controller Mode {ctr_mode}")


def update_mode_detumbling(current_mode) -> int:
    """
    Returns the current mode of the ADCS for a detumbling-only controller
    """
    gyro_status, omega = sensors.read_gyro()

    # Fail-safe STABLE mode if IMU fails
    if gyro_status != StatusConst.OK:
        return Modes.STABLE

    omega_norm = np.linalg.norm(omega)

    if current_mode == Modes.TUMBLING:
        if omega_norm <= Modes.TUMBLING_TOL:
            return Modes.STABLE
        return Modes.TUMBLING

    if current_mode == Modes.STABLE:
        if omega_norm >= Modes.TUMBLING_TOL:
            return Modes.TUMBLING
        if omega_norm < Modes.DETUMBLED_TOL_LO:
            return Modes.ACS_OFF
        return Modes.STABLE

    if current_mode == Modes.ACS_OFF:
        if omega_norm >= Modes.TUMBLING_TOL:
            return Modes.TUMBLING
        if omega_norm >= Modes.DETUMBLED_TOL_HI:
            return Modes.STABLE
        return Modes.ACS_OFF

    raise ValueError(f"Invalid Current Mode {current_mode}")


def update_mode_sun_pointing(current_mode) -> int:
    """
    Returns the current mode of the ADCS for a spin-stabilized sun-pointing controller
    """
    gyro_status, omega = sensors.read_gyro()
    sun_status, sun_pos_body, _ = sensors.read_sun_position()

    # Fail-safe STABLE mode if IMU or sun acquisition fails
    if gyro_status != StatusConst.OK:
        return Modes.STABLE

    omega_norm = np.linalg.norm(omega)

    if current_mode == Modes.TUMBLING:
        if omega_norm <= Modes.TUMBLING_TOL:
            return Modes.STABLE
        return Modes.TUMBLING

    if current_mode == Modes.STABLE:
        h_hat = np.dot(ControllerConst.INERTIA_MAT, omega) / ControllerConst.MOMENTUM_TARGET_MAG
        momentum_error = np.linalg.norm(ControllerConst.INERTIA_MAJOR_DIR - h_hat)
        if omega_norm >= Modes.TUMBLING_TOL:
            return Modes.TUMBLING
        if momentum_error <= Modes.STABLE_TOL_LO and sun_status == StatusConst.OK:
            return Modes.SUN_POINTING
        return Modes.STABLE

    if current_mode == Modes.SUN_POINTING:
        h_hat = np.dot(ControllerConst.INERTIA_MAT, omega) / ControllerConst.MOMENTUM_TARGET_MAG
        momentum_error = np.linalg.norm(ControllerConst.INERTIA_MAJOR_DIR - h_hat)

        if momentum_error >= Modes.STABLE_TOL_LO:
            return Modes.STABLE

        if sun_status != StatusConst.OK:
            return Modes.SUN_POINTING

        h = np.dot(ControllerConst.INERTIA_MAT, omega)
        h_norm = np.linalg.norm(h)
        if h_norm == 0:
            return Modes.SUN_POINTING

        h_hat = h / h_norm  # conical condition
        sun_error = np.linalg.norm(sun_pos_body - h_hat)

        if sun_status == StatusConst.OK and sun_error <= Modes.SUN_POINTED_TOL_LO:
            return Modes.ACS_OFF

        return Modes.SUN_POINTING

    if current_mode == Modes.ACS_OFF:
        h_hat = np.dot(ControllerConst.INERTIA_MAT, omega) / ControllerConst.MOMENTUM_TARGET_MAG
        momentum_error = np.linalg.norm(ControllerConst.INERTIA_MAJOR_DIR - h_hat)
        if momentum_error >= Modes.STABLE_TOL_HI:
            return Modes.STABLE
        if sun_status == StatusConst.OK:
            h = np.dot(ControllerConst.INERTIA_MAT, omega)
            h_norm = np.linalg.norm(h)
            if h_norm == 0:
                return Modes.SUN_POINTING
            h_hat = h / h_norm  # conical condition
            sun_error = np.linalg.norm(sun_pos_body - h_hat)
            if sun_error >= Modes.SUN_POINTED_TOL_HI:
                return Modes.SUN_POINTING
            return Modes.ACS_OFF
        return Modes.ACS_OFF

    raise ValueError(f"Invalid Current Mode {current_mode}")
