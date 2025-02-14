"""
This module will provide online orbit tracking/propagation capabilities based on a simple dynamics model.
It leverages orbit information, either from the GPS module or uplinked information from the groud.

"""

from apps.adcs.consts import StatusConst
from ulab import numpy as np


class OrbitPropagator:

    # Storage
    last_update_time = 0
    last_updated_state = np.zeros((6,))

    # Propagation settings
    min_timestep = 1  # seconds
    initialized = False

    @classmethod
    def acceleration(cls, state):
        # Earth Constants
        mu_earth = 3.986004418e14  # m^3s^-2 Earth standard gravitational parameter

        acc = -(mu_earth / (np.linalg.norm(state[0:3]) ** 3)) * state[0:3]
        return acc

    @classmethod
    def propagate_orbit(cls, current_time: int, last_gps_time: int = None, last_gps_state: np.ndarray = None):

        if last_gps_state is not None:
            cls.last_updated_state = last_gps_state
            cls.last_update_time = last_gps_time

            if not cls.initialized:
                cls.initialized = True
        else:
            if not cls.initialized:
                return StatusConst.OPROP_INIT_FAIL, np.zeros((3,)), np.zeros((3,))

        # Propagate orbit
        num_steps = (cls.last_update_time - current_time) // cls.min_timestep
        if num_steps >= 20:
            num_steps = 20
            timestep = (cls.last_update_time - current_time) / num_steps
        else:
            timestep = cls.min_timestep

        for _ in range(num_steps):
            # Update state based on Euler integration
            state_derivative = np.concatenate((cls.acceleration(cls.last_updated_state), cls.last_updated_state[3:6]))
            cls.last_updated_state = cls.last_updated_state + timestep * state_derivative

        fractional_state_update = ((cls.last_update_time - current_time) % timestep) * np.concatenate(
            (cls.acceleration(cls.last_updated_state), cls.last_updated_state[3:6])
        )
        cls.last_updated_state = cls.last_updated_state + fractional_state_update
        cls.last_update_time = current_time

        return StatusConst.OK, cls.last_updated_state[0:3], cls.last_updated_state[3:6]
