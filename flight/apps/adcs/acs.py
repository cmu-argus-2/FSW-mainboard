"""
Attitude Control Module for the Attitude Determination and Control Subsystem (ADCS).

This module is responsible for computing voltage allocations to each of ARGUS' 6 magnetorquer coils.
"""

from apps.adcs.consts import ControllerConst
from hal.configuration import SATELLITE
from ulab import numpy as np


def readings_are_valid(
    readings,  #: tuple[np.ndarray],
) -> bool:
    for reading in readings:
        if not isinstance(reading, np.ndarray) or reading.shape != ControllerConst.READING_DIM:
            return False
    return True


def spin_stabilizing_controller(omega: np.ndarray, mag_field: np.ndarray) -> np.ndarray:
    """
    Spin-stabilizing control law.
    Augmented with tanh function for soft clipping.
    Returns a normalized throttle command for the magnetorquers.
    All sensor estimates are in the body-fixed reference frame.
    """
    # Stop ACS if the reading values are invalid
    if not readings_are_valid((omega, mag_field)):
        return ControllerConst.FALLBACK_CONTROL

    # Do spin stabilization
    else:
        # Compute angular momentum error
        error = ControllerConst.MOMENTUM_TARGET - np.dot(ControllerConst.INERTIA_MAT, omega)

        # Compute B-cross dipole moment
        u = ControllerConst.SPIN_STABILIZING_GAIN * np.cross(mag_field, error)

        # Smooth the controller while enforcing an l2-norm upper bound on the control input
        return smooth_throttle(u)


def sun_pointing_controller(sun_vector: np.ndarray, omega: np.ndarray, mag_field: np.ndarray) -> np.ndarray:
    """
    Sun pointing control law.
    Augmented with tanh function for soft clipping.
    All sensor estimates are in the body-fixed reference frame.
    """
    # Stop ACS if the reading values are invalid
    if (
        not readings_are_valid((sun_vector, omega, mag_field))
        # or np.linalg.norm(mag_field) == 0
        or np.linalg.norm(sun_vector) == 0
        or np.linalg.norm(omega) == 0
    ):
        return ControllerConst.FALLBACK_CONTROL

    # Do sun pointing
    else:
        # Compute pointing error
        ang_mom = np.dot(ControllerConst.INERTIA_MAT, omega)
        # conical projection of angular momentum onto sun vector
        error = sun_vector - ang_mom / np.linalg.norm(ang_mom)
        # spherical projection of angular momentum onto sun vector
        # error = sun_vector - np.dot(PhysicalConst.INERTIA_MAT, omega) / np.linalg.norm(ControllerConst.MOMENTUM_TARGET)

        # Compute controller using bang-bang control law
        u_dir = np.cross(mag_field, error)
        u_dir_norm = np.linalg.norm(u_dir)

        if u_dir_norm < 1e-8:
            # Return zeros to avoid division by zero
            return ControllerConst.FALLBACK_CONTROL
        else:
            # Normalize the control input
            return u_dir / u_dir_norm


_DERIVATIVE_WEIGHTS = np.array([-5.0, -3.0, -1.0, 1.0, 3.0, 5.0]) / 35.0


def bdot_controller(mag_buffer: np.ndarray, dt: float) -> np.ndarray:
    """
    B-dot control law using a 6-point central derivative over uniformly-spaced samples.
    mag_buffer: shape (6, 3), oldest sample in row 0.
    dt: uniform sample spacing in seconds.
    """
    if mag_buffer.shape != (6, 3) or dt <= 0:
        return ControllerConst.FALLBACK_CONTROL
    b_dot = np.dot(mag_buffer.T, _DERIVATIVE_WEIGHTS) / dt
    u = -ControllerConst.DETUMB_GAIN * b_dot
    return smooth_throttle(u)


def bcross_controller(mag_field: np.ndarray, omega: np.ndarray) -> np.ndarray:
    """
    B-cross control law.
    """
    if not readings_are_valid((omega, mag_field)):
        return ControllerConst.FALLBACK_CONTROL

    u = -ControllerConst.DETUMB_GAIN * np.cross(mag_field, omega)
    return smooth_throttle(u)


def smooth_throttle(u: np.ndarray) -> np.ndarray:
    """
    Applies a smooth saturation function to the control input u, ensuring that
    its magnitude does not exceed one.
    """
    u_norm = np.linalg.norm(u)
    if u_norm == 0:
        return u
    return u * np.tanh(u_norm) / u_norm


_MCM_FACES = ("XP", "XM", "YP", "YM", "ZP", "ZM")
_COIL_STATUS = [False] * 6
_U_EFF = np.zeros(3)


def mcm_coil_allocator(u: np.ndarray, b: np.ndarray) -> list:
    # Step 1: query coil availability per axis pair
    for n in range(3):
        _COIL_STATUS[2 * n] = SATELLITE.TORQUE_DRIVERS_AVAILABLE(_MCM_FACES[2 * n])
        _COIL_STATUS[2 * n + 1] = SATELLITE.TORQUE_DRIVERS_AVAILABLE(_MCM_FACES[2 * n + 1])

    # Step 2: find a fully failed axis; only single-axis failure is compensated
    axis_fail = -1
    for axis in range(3):
        if not (_COIL_STATUS[2 * axis] or _COIL_STATUS[2 * axis + 1]):
            if axis_fail < 0:
                axis_fail = axis
            else:
                axis_fail = -2  # two axes failed — no compensation attempted
                break

    # Step 3: copy u into persistent buffer; project out failed-axis component along b
    # u_eff = u - (u[a] / b[a]) * b  →  zeros the failed-axis dipole, redistributes along b
    _U_EFF[0] = u[0]
    _U_EFF[1] = u[1]
    _U_EFF[2] = u[2]
    if axis_fail >= 0 and abs(b[axis_fail]) > 1e-9:
        factor = _U_EFF[axis_fail] / b[axis_fail]
        _U_EFF[0] -= factor * b[0]
        _U_EFF[1] -= factor * b[1]
        _U_EFF[2] -= factor * b[2]

    # Step 4: compute effective coil-vector L2 norm to enforce power limit
    # both coils on axis → each gets 0.5*val  (contributes 0.5*val^2 to norm^2)
    # single coil on axis → it gets 1.0*val   (contributes val^2)
    norm_sq = 0.0
    for axis in range(3):
        val = _U_EFF[axis]
        if _COIL_STATUS[2 * axis] and _COIL_STATUS[2 * axis + 1]:
            norm_sq += 0.5 * val * val
        elif _COIL_STATUS[2 * axis] or _COIL_STATUS[2 * axis + 1]:
            norm_sq += val * val
    scale = max(1.0, norm_sq ** 0.5 * 0.707)

    # Step 5: distribute scaled throttle to coils
    for axis in range(3):
        ep = _COIL_STATUS[2 * axis]
        em = _COIL_STATUS[2 * axis + 1]
        val = _U_EFF[axis] / scale
        if ep and em:
            SATELLITE.APPLY_MAGNETIC_CONTROL(_MCM_FACES[2 * axis], 0.5 * val)
            SATELLITE.APPLY_MAGNETIC_CONTROL(_MCM_FACES[2 * axis + 1], 0.5 * val)
        elif ep:
            SATELLITE.APPLY_MAGNETIC_CONTROL(_MCM_FACES[2 * axis], val)
        elif em:
            SATELLITE.APPLY_MAGNETIC_CONTROL(_MCM_FACES[2 * axis + 1], val)

    return _COIL_STATUS


def zero_all_coils():
    """
    Sets all magnetorquer coil throttles to zero.
    """
    for face in _MCM_FACES:
        if SATELLITE.TORQUE_DRIVERS_AVAILABLE(face):
            SATELLITE.APPLY_MAGNETIC_CONTROL(face, 0)
