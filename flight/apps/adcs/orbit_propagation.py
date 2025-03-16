"""
This module will provide online orbit tracking/propagation capabilities based on a simple dynamics model.
It leverages orbit information, either from the GPS module or uplinked information from the groud.

"""

from apps.adcs.consts import StatusConst
from apps.adcs.utils import is_valid_gps_state
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
            pre_reboot_state = pre_reboot_fix[GPS_IDX.GPS_ECI_X : GPS_IDX.GPS_ECI_VZ + 1]

            # Compute validity of GPS measurements
            if pre_reboot_time is not None and is_valid_gps_state(pre_reboot_state[0:3], pre_reboot_state[3:6]):
                last_updated_state = pre_reboot_state
                last_update_time = pre_reboot_time
                initialized = True

    @classmethod
    def propagate_orbit(cls, current_time: int, last_gps_time: int = None, last_gps_state_eci: np.ndarray = None):
        if current_time is None:
            return StatusConst.OPROP_INIT_FAIL, np.zeros((3,)), np.zeros((3,))

        if (
            last_gps_state_eci is not None
            and is_valid_gps_state(last_gps_state_eci[0:3], last_gps_state_eci[3:6])
            and last_gps_time is not None
        ):
            cls.last_updated_state = last_gps_state_eci
            cls.last_update_time = last_gps_time

            if not cls.initialized:
                cls.initialized = True
        else:
            if not cls.initialized:
                return StatusConst.OPROP_INIT_FAIL, np.zeros((3,)), np.zeros((3,))

        # Propagate orbit
        position_norm = np.linalg.norm(cls.last_updated_state[0:3])
        velocity_norm = np.linalg.norm(cls.last_updated_state[3:6])

        if not is_valid_gps_state(cls.last_updated_state[0:3], cls.last_updated_state[3:6]):
            # Somehow, we have messed up so bad that our position and/or velocity vectors are garbage.
            # Reset OrbitProp and wait for a valid GPS fix
            cls.initialized = False
            cls.last_updated_state = np.zeros((6,))
            return StatusConst.OPROP_INIT_FAIL, np.zeros((3,)), np.zeros((3,))

        # Calculate omega (angular velocity) vector
        omega = np.cross(cls.last_updated_state[0:3], cls.last_updated_state[3:6]) / position_norm**2

        # Calculate rotation angle about omega
        theta = np.linalg.norm(omega) * (current_time - cls.last_update_time)

        # Rotate position about omega by angle theta
        cls.last_updated_state[0:3] = position_norm * (
            cls.last_updated_state[0:3] * np.cos(theta) / position_norm
            + cls.last_updated_state[3:6] * np.sin(theta) / velocity_norm
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
