from core.state_machine import STATES
from ulab import numpy as np

""" Contains functions to check the preconditions of Commands """

_TIME_RANGE_LOW = 1577836800
_TIME_RANGE_HIGH = 1893456000
PRECONDITION_REGISTRY = {}


def register_precondition(name=None):
    """Decorator to register a precondition function in PRECONDITION_REGISTRY."""

    def decorator(func):
        precondition_name = name or func.__name__
        PRECONDITION_REGISTRY[precondition_name] = func
        return func

    return decorator


@register_precondition()
def valid_inputs(*args) -> bool:
    """
    Precondition for SUM command.
    Checks that the inputs are integers or floats.
    """
    opA = args[0]
    opB = args[1]
    if (isinstance(opA, (int, float))) and (isinstance(opB, (int, float))):
        return True
    else:
        return False


@register_precondition()
def valid_state(*args) -> bool:
    """
    Precondition for SWITCH_TO_STATE command.
    Will check that the target_state_id is actually one of the states
    """
    target_state_id = args[0]
    return STATES.STARTUP <= target_state_id <= STATES.LOW_POWER


@register_precondition()
def valid_time_format(*args) -> bool:
    """
    Precondition for UPLINK_TIME_REFERENCE / UPLINK_ORBIT_TIME_REFERENCE commands.
    Will check that time is of proper UNIX format
    """
    time_reference = args[0]

    if not isinstance(time_reference, int):
        return False

    """
    Since CPy time.time() starts on Jan 1st 2020,
    limit the time reference to at least this date.

    Can also update this to be our launch date,
    although that will lead to issues in testing
    while in development.
    """

    # Check that the timestamp is above Jan 1st 2020 UTC
    # Check that the timestamp is below Jan 1st 2030 UTC
    if _TIME_RANGE_LOW < time_reference < _TIME_RANGE_HIGH:
        return True
    else:
        return False


@register_precondition()
def valid_adcs_mode(*args) -> bool:
    """
    Precondition for ADCS_CTRL_MODE command.
    Checks that the mode_id is a valid ADCS controller mode.
    """
    mode_id = args[0]
    return (isinstance(mode_id, int)) and 0 <= mode_id <= 2


@register_precondition()
def valid_gains(*args) -> bool:
    """
    Precondition for ADCS_UPDATE_GAINS command.
    Checks that the gains are valid.
    """
    k_ss = args[0]
    k_dtb = args[1]
    if (isinstance(k_ss, (int, float))) and (isinstance(k_dtb, (int, float))):
        if k_ss >= 0 and k_dtb >= 0:
            return True
    return False


@register_precondition()
def valid_w_tgt(*args) -> bool:
    """
    Precondition for ADCS_UPDATE_OMEGA_TARGET command.
    Checks that the omega magnitude target is valid.
    """
    omega_mag_target = args[0]
    if isinstance(omega_mag_target, (int, float)):
        if omega_mag_target >= 0:
            return True
    return False


@register_precondition()
def valid_inertia(*args) -> bool:
    """
    Precondition for ADCS_UPDATE_INERTIA command.
    Checks that the inertia values are valid.
    """
    ixx = args[0]
    ixy = args[1]
    ixz = args[2]
    iyy = args[3]
    iyz = args[4]
    izz = args[5]

    if all(isinstance(val, (int, float)) for val in [ixx, ixy, ixz, iyy, iyz, izz]):
        return True

    # compute eigenvalues to check that inertia matrix is positive definite
    inertia_matrix = np.array([[ixx, ixy, ixz], [ixy, iyy, iyz], [ixz, iyz, izz]])
    eigvals = np.linalg.eigvals(inertia_matrix)
    if np.any(eigvals <= 0):
        return False

    # no eigenvalue can be greater than the sum of the other two
    if np.any(eigvals >= np.sum(eigvals) - eigvals):
        return False

    return False


@register_precondition()
def valid_vfd_tols(*args) -> bool:
    """Precondition for Very Fast Detumbling Mode transition tolerances. Checks that the tolerances are valid."""
    vf_bdot = args[0]
    vf = args[1]
    if (isinstance(vf_bdot, (int, float))) and (isinstance(vf, (int, float))):
        if vf_bdot >= 0 and vf >= 0:
            return True
    return False


@register_precondition()
def valid_det_tols(*args) -> bool:
    """Precondition for Detumbling Mode transition tolerances. Checks that the tolerances are valid."""
    tb = args[0]
    dtb_lo = args[1]
    dtb_hi = args[2]
    if (isinstance(tb, (int, float))) and (isinstance(dtb_lo, (int, float))) and (isinstance(dtb_hi, (int, float))):
        if tb >= 0 and dtb_lo >= 0 and dtb_hi >= 0 and dtb_lo < dtb_hi and dtb_hi < tb:
            # still a risk if tb > vf_tb tolerances. It is assumed the operator will be aware of this
            return True
    return False


@register_precondition()
def valid_tols(*args) -> bool:
    """Precondition for stable and sun pointed transition tolerances. Checks that the tolerances are valid."""
    lo = args[0]
    hi = args[1]
    if (isinstance(lo, float)) and (isinstance(hi, float)):
        if lo >= 0 and hi >= 0 and lo < hi and hi <= 1.0:
            return True
    return False


# TODO: add a precondition for OD experiment (no OD should be in progress)
