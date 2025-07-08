"""
Attitude Control Module for the Attitude Determination and Control Subsystem (ADCS).

This module is responsible for computing voltage allocations to each of ARGUS' 6 magnetorquer coils.
"""

from apps.adcs.consts import ControllerConst, MCMConst, PhysicalConst
from hal.configuration import SATELLITE
from ulab import numpy as np


# TODO: test on mainboard
def readings_are_valid(
    readings: tuple[np.ndarray],
) -> bool:
    for reading in readings:
        if not isinstance(reading, np.ndarray) or reading.shape != ControllerConst.READING_DIM:
            return False
    return True


def spin_stabilizing_controller(omega: np.ndarray, mag_field: np.ndarray) -> np.ndarray:
    """
    B-cross law: https://arc.aiaa.org/doi/epdf/10.2514/1.53074.
    Augmented with tanh function for soft clipping.
    All sensor estimates are in the body-fixed reference frame.
    """
    # Stop ACS if the reading values are invalid
    if (
        not readings_are_valid((omega, mag_field))
        or np.linalg.norm(mag_field) == 0
        or np.linalg.norm(omega) <= ControllerConst.OMEGA_TOLERANCE
    ):
        return ControllerConst.FALLBACK_CONTROL

    # Do spin stabilization
    else:
        # Compute angular momentum error
        error = ControllerConst.MOMENTUM_TARGET - np.dot(PhysicalConst.INERTIA_MAT, omega)

        # Compute B-cross dipole moment
        u = ControllerConst.SPIN_STABILIZING_GAIN * np.cross(mag_field, error)

        # Smoothly normalize the control input
        return np.tanh(u)


def sun_pointing_controller(sun_vector: np.ndarray, omega: np.ndarray, mag_field: np.ndarray) -> np.ndarray:
    # Stop ACS if the reading values are invalid
    if (
        not readings_are_valid((sun_vector, omega, mag_field))
        or np.linalg.norm(mag_field) == 0
        or np.linalg.norm(sun_vector) == 0
        or np.linalg.norm(omega) <= ControllerConst.OMEGA_TOLERANCE
    ):
        return ControllerConst.FALLBACK_CONTROL

    # Do sun pointing
    else:
        # Compute pointing error
        error = sun_vector - np.dot(PhysicalConst.INERTIA_MAT, omega) / np.linalg.norm(ControllerConst.MOMENTUM_TARGET)

        # Compute controller using bang-bang control law
        u_dir = np.cross(mag_field, error)
        u_dir_norm = np.linalg.norm(u_dir)

        if u_dir_norm < 1e-8:
            # Return zeros to avoid division by zero
            return ControllerConst.FALLBACK_CONTROL
        else:
            # Normalize the control input
            return u_dir / u_dir_norm


def mcm_coil_allocator(u: np.ndarray) -> np.ndarray:
    # Query the available coil statuses
    coil_status = []
    mcm_alloc = np.zeros((6, 3))

    for n in range(MCMConst.N_MCM // 2):
        EP_status = SATELLITE.TORQUE_DRIVERS_AVAILABLE(MCMConst.MCM_FACES[2 * n])
        EM_status = SATELLITE.TORQUE_DRIVERS_AVAILABLE(MCMConst.MCM_FACES[2 * n + 1])

        if EP_status and EM_status:
            mcm_alloc[2 * n, :] = MCMConst.ALLOC_MAT[2 * n, :]
            mcm_alloc[2 * n + 1, :] = MCMConst.ALLOC_MAT[2 * n + 1, :]
        elif EP_status and not EM_status:
            mcm_alloc[2 * n, :] = 2 * MCMConst.ALLOC_MAT[2 * n, :]
            mcm_alloc[2 * n + 1, :] = np.zeros((1, 3))
        elif not EP_status and EM_status:
            mcm_alloc[2 * n, :] = np.zeros((1, 3))
            mcm_alloc[2 * n + 1, :] = 2 * MCMConst.ALLOC_MAT[2 * n + 1, :]
        else:
            mcm_alloc[2 * n : 2 * (n + 1)] = np.zeros((2, 3))

        coil_status = coil_status + [EP_status, EM_status]

    # Compute Coil Voltages based on Allocation matrix and target input
    u_throttle = np.dot(mcm_alloc, u)
    u_throttle = np.clip(u_throttle, -1, 1)

    # Apply Coil Voltages
    for n in range(MCMConst.N_MCM):
        if coil_status[n]:
            SATELLITE.APPLY_MAGNETIC_CONTROL(MCMConst.MCM_FACES[n], u_throttle[n])

    return coil_status


def zero_all_coils():
    for face in MCMConst.MCM_FACES:
        if SATELLITE.TORQUE_DRIVERS_AVAILABLE(face):
            SATELLITE.APPLY_MAGNETIC_CONTROL(face, 0)
