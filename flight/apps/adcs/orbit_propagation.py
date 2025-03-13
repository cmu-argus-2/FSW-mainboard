"""
This module will provide online orbit tracking/propagation capabilities based on a simple dynamics model.
It leverages orbit information, either from the GPS module or uplinked information from the groud.

"""

from apps.adcs.consts import StatusConst
from apps.adcs.frames import ecef_to_eci
from apps.telemetry.constants import GPS_IDX
from core import DataHandler as DH
from ulab import numpy as np


class OrbitPropagator:
    # Storage
    last_update_time = 0
    last_updated_state = np.zeros((6,))

    # Propagation settings
    min_timestep = 1  # seconds
    initialized = False

    # If Reboot, check log for a pre-existing GPS fix
    if DH.data_process_exists("gps"):
        pre_reboot_fix = DH.get_latest_data("gps")
        if pre_reboot_fix is not None:
            pre_reboot_time = pre_reboot_fix[GPS_IDX.TIME_GPS]
            pre_reboot_state = 1e-2 * pre_reboot_fix[GPS_IDX.GPS_ECEF_X : GPS_IDX.GPS_ECEF_VZ + 1]

            # Compute validity of GPS measurements
            if pre_reboot_state[0:3] is None or pre_reboot_state[3:6] is None:
                pass
            elif not (6.0e6 <= np.linalg.norm(pre_reboot_state[0:3]) <= 7.5e6) or not (
                3.0e3 <= np.linalg.norm(pre_reboot_state[3:6]) <= 1.0e4
            ):
                pass
            else:
                last_update_time = pre_reboot_time
                Recef2eci = ecef_to_eci(last_update_time)
                last_updated_state[0:3] = np.dot(Recef2eci, pre_reboot_state[0:3])
                last_updated_state[3:6] = np.dot(Recef2eci, pre_reboot_state[3:6])
                initialized = True

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
        position_norm = np.linalg.norm(cls.last_updated_state[0:3])
        velocity_norm = np.linalg.norm(cls.last_updated_state[3:6])

        if not (6.0e6 <= position_norm <= 7.5e6 and 3.0e3 <= velocity_norm <= 1.0e4):
            # Somehow, we have messed up so bad that our position and/or velocity vectors are garbage.
            # Reset OrbitProp and wait for a valid GPS fix
            cls.initialized = False
            return StatusConst.OPROP_INIT_FAIL, np.zeros((3,)), np.zeros((3,))

        # Calculate omega (angular velocity) vector
        omega = np.cross(cls.last_updated_state[0:3], cls.last_updated_state[3:6]) / position_norm**2

        # Calculate rotation angle about omega
        theta = omega * (cls.last_update_time - current_time)

        # Rotate position about omega by angle theta
        cls.last_updated_state[0:3] = position_norm * (
            np.cos(theta) + cls.last_updated_state[3:6] * np.sin(theta) / velocity_norm
        )

        # Compute velocity using (v = omega x r)
        cls.last_updated_state[3:6] = np.cross(omega, cls.last_updated_state[0:3])

        return StatusConst.OK, cls.last_updated_state[0:3], cls.last_updated_state[3:6]

    @classmethod
    def set_last_update_time(cls, updated_time):
        """
        Update the last_update_time variable with a time reference
        """
        cls.last_update_time = updated_time

    @classmethod
    def set_last_updated_state(cls, updated_state: np.ndarray):
        """
        Update the last_updated_state variable with orbital position and velocity
        """
        cls.last_updated_state = updated_state
