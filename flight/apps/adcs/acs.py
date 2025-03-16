"""
Attitude Control Module for the Attitude Determination and Control Subsystem (ADCS).

This module is responsible for computing voltage allocations to each of ARGUS' 6 magnetorquer coils.
"""

from apps.adcs.consts import ControllerConst, MCMConst, PhysicalConst
from hal.configuration import SATELLITE
from ulab import numpy as np


def spin_stabilizing_controller(omega: np.ndarray, mag_field: np.ndarray) -> np.ndarray:
    """
    B-cross law: https://arc.aiaa.org/doi/epdf/10.2514/1.53074.
    Augmented with tanh function for soft clipping.
    All sensor estimates are in the body-fixed reference frame.
    """

    if np.linalg.norm(mag_field) == 0:  # Stop ACS if the field value is invalid
        u_dir = np.zeros((3,))

    else:
        # Compute Angular Momentum error
        error = PhysicalConst.INERTIA_MAJOR_DIR - np.dot(PhysicalConst.INERTIA_MAT, omega) / ControllerConst.MOMENTUM_TARGET

        # Compute controller using B-cross
        u_dir = ControllerConst.SPIN_STABILIZING_GAIN * np.cross(mag_field, error)

        # Smooth controller using tanh
        u_dir = np.tanh(u_dir)

    coil_status = mcm_coil_allocator(u_dir)

    return coil_status


def sun_pointed_controller(sun_vector: np.ndarray, omega: np.ndarray, mag_field: np.ndarray) -> np.ndarray:
    if np.linalg.norm(mag_field) == 0 or np.linalg.norm(sun_vector) == 0:  # Stop ACS if either field is invalid
        u_dir = np.zeros((3,))
    else:
        # Compute Pointing Error
        error = sun_vector - np.dot(PhysicalConst.INERTIA_MAT, omega) / ControllerConst.MOMENTUM_TARGET

        # Compute controller using bang-bang control law
        u_dir = np.cross(mag_field, error)
        u_dir_norm = np.linalg.norm(u_dir)

        if u_dir_norm < 1e-6:
            u_dir = np.zeros((3,))
        else:
            u_dir = u_dir / u_dir_norm

    coil_status = mcm_coil_allocator(u_dir)

    return coil_status


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
