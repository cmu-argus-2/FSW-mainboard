"""
This module will provide online orbit tracking/propagation capabilities based on a simple dynamics model.
It leverages orbit information, either from the GPS module or uplinked information from the groud.

"""

from apps.adcs.consts import StatusConst
from apps.adcs.frames import convert_ecef_state_to_eci
from apps.adcs.utils import is_valid_gps_state
from apps.telemetry.constants import GPS_IDX
from core import DataHandler as DH
from hal.configuration import SATELLITE
from ulab import numpy as np


class OrbitPropagator:
    # Storage
    last_update_time = 0
    last_updated_state = np.zeros((6,))
    last_valid_gps_time = 0

    # Propagation settings
    min_timestep = 1  # seconds
    initialized = False

    @classmethod
    def update_position(cls, current_time: int) -> np.ndarray:
        gps_status, gps_record_time, gps_pos_eci, gps_vel_eci = cls.read_gps()

        if gps_status != StatusConst.OK:
            status, pos_eci, vel_eci = cls.propagate_orbit(current_time, None, None)
        else:
            status, pos_eci, vel_eci = cls.propagate_orbit(
                current_time, gps_record_time, np.concatenate((gps_pos_eci, gps_vel_eci))
            )

        return status, pos_eci, vel_eci

    @classmethod
    def read_gps(cls):
        # Read GPS process
        if DH.data_process_exists("gps") and SATELLITE.GPS_AVAILABLE:
            # Get last GPS update time and position at that time
            gps_data = DH.get_latest_data("gps")

            if gps_data is not None:
                gps_record_time = gps_data[GPS_IDX.TIME_GPS]
                gps_pos_ecef = 1e-2 * np.array(gps_data[GPS_IDX.GPS_ECEF_X : GPS_IDX.GPS_ECEF_Z + 1]).reshape(
                    (3,)
                )  # Convert from cm to m
                gps_vel_ecef = 1e-2 * np.array(gps_data[GPS_IDX.GPS_ECEF_VX : GPS_IDX.GPS_ECEF_VZ + 1]).reshape(
                    (3,)
                )  # Convert from cm/s to m/s

                # Sensor validity check
                if not is_valid_gps_state(gps_pos_ecef, gps_vel_ecef):
                    return StatusConst.GPS_FAIL, 0, np.zeros((3,)), np.zeros((3,))
                else:
                    # Convert ECEF to ECI
                    gps_pos_eci, gps_vel_eci = convert_ecef_state_to_eci(gps_pos_ecef, gps_vel_ecef, gps_record_time)

                    return StatusConst.OK, gps_record_time, gps_pos_eci, gps_vel_eci
            else:
                return StatusConst.GPS_FAIL, 0, np.zeros((3,)), np.zeros((3,))
        else:
            return StatusConst.GPS_FAIL, 0, np.zeros((3,)), np.zeros((3,))

    @classmethod
    def propagate_orbit(cls, current_time: int, last_gps_time: int = None, last_gps_state_eci: np.ndarray = None):
        """
        Estimates the current position and velocity in ECI frame from a last known GPS fix

        1. If a GPS fix was already used, then the state is propagated forward from a previous estimate
        2. If the GPS fix is new, the state is directly set to it and forward propagated from that reference

        INPUTS:
        1. current_time : int, current unix timestamp
        2. last_gps_time : int, unix timestamp of the last gps fix
        3. last_gps_state_eci : np.ndarray (6,), 6x1 [position (m), velocity (m/s)] ECI state at the last gps fix
        """

        # If the current ime is None, fail and exit
        if current_time is None:
            return StatusConst.OPROP_INIT_FAIL, np.zeros((3,)), np.zeros((3,))

        # If a valid gps fix is provided and it is previously unused, force update the state estimate to the gps state
        if (
            last_gps_time != cls.last_valid_gps_time
            and last_gps_state_eci is not None
            and is_valid_gps_state(last_gps_state_eci[0:3], last_gps_state_eci[3:6])
            and last_gps_time is not None
        ):
            cls.last_updated_state = last_gps_state_eci
            cls.last_update_time = last_gps_time
            cls.last_valid_gps_time = last_gps_time

            # Initialize the Orbit Prop with the valid GPS fix
            if not cls.initialized:
                cls.initialized = True
        else:
            # If Orbit Prop is not initialized and a valid gps fix was not provided, fail and exit
            if not cls.initialized:
                return StatusConst.OPROP_INIT_FAIL, np.zeros((3,)), np.zeros((3,))

        # Propagate orbit from the last state estimate
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

        # Update last update time
        cls.last_update_time = current_time

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
