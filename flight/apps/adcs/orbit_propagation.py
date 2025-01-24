"""
This module will provide online orbit tracking/propagation capabilities based on a simple dynamics model.
It leverages orbit information, either from the GPS module or uplinked information from the groud.

"""

from ulab import numpy as np


def acceleration(state):
    # Earth Constants
    mu_earth = 3.986004418e14  # m^3s^-2 Earth standard gravitational parameter

    acc = -mu_earth * (np.linalg.norm(state[0:3]) ** 3) * state[0:3]
    return acc


def propagate_orbit(
    current_time: int, last_update_time: int, last_updated_position: np.ndarray, last_updated_velocity: np.ndarray
) -> np.ndarray:

    # Integration settings
    timestep = 1  # seconds
    num_steps = (last_update_time - current_time) // timestep

    state = np.concatenate(last_updated_position, last_updated_velocity)

    for _ in range(num_steps):
        # Update state based on Euler integration
        state_derivative = np.concatenate(acceleration(state), state[3:6])
        state = state + timestep * state_derivative

    state = state + ((last_update_time - current_time) % timestep) * np.concatenate(acceleration(state), state[3:6])

    return state[0:3], state[3:6]
