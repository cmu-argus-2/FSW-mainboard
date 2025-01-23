"""

Attitude Determination Module for the Attitude Determination and Control Subsystem (ADCS).

This module is responsible for processing GNC sensor data to determine the satellite's attitude.

Argus possesses a 3-axis IMU (Inertial Measurement Unit) providing angular rate, acceleration, and
magnetic field data on the mainboard.

"""

from ulab import numpy as np


def rotm2quat(r):
    """
    Convert a rotation matrix to a quaternion.

    Args:
        r (np.ndarray): Rotation matrix.

    Returns:
        np.ndarray: Quaternion [q0, q1, q2, q3].
    """
    q = np.zeros(4)
    q[0] = 0.5 * np.sqrt(1 + r[0, 0] + r[1, 1] + r[2, 2])
    q[1] = (1 / (4 * q[0])) * (r[2][1] - r[1][2])
    q[2] = (1 / (4 * q[0])) * (r[0][2] - r[2][0])
    q[3] = (1 / (4 * q[0])) * (r[1][0] - r[0][1])
    return np.array(q)


def TRIAD(n1, n2, b1, b2):

    n1 = np.array(n1)
    n2 = np.array(n2)
    b1 = np.array(b1)
    b2 = np.array(b2)

    # Normalize the input vectors
    n1 /= np.linalg.norm(n1)
    n2 /= np.linalg.norm(n2)
    b1 /= np.linalg.norm(b1)
    b2 /= np.linalg.norm(b2)

    # Inertial triad
    t1 = n1
    t2 = np.cross(n1, n2) / np.linalg.norm(np.cross(n1, n2))  # Third linearly independant vector
    t3 = np.cross(t1, t2) / np.linalg.norm(np.cross(t1, t2))
    T = np.array([t1, t2, t3]).transpose()

    # Body triad
    w1 = b1
    w2 = np.cross(b1, b2) / np.linalg.norm(np.cross(b1, b2))
    w3 = np.cross(w1, w2) / np.linalg.norm(np.cross(w1, w2))
    W = np.array([w1, w2, w3]).transpose()

    # Determine attitude
    Q = np.dot(T, W.transpose())

    return rotm2quat(Q)

import time
from ulab import numpy as np

from core import DataHandler as DH
from hal.configuration import SATELLITE
from apps.telemetry.constants import GPS_IDX
from apps.adcs.frames import ecef_to_eci
from apps.adcs.orbit_propagation import propagate_orbit

"""
    Attitude Determination Class
    
    Contains functions for the following:
        - Initializing the MEKF
        - Reading Sensors
        - Propagating MEKF
"""
class AttitudeDetermination:
    
    # Initialized Flag to retry initialization
    initialized = False
    
    # State
    estimated_state = np.zeros((19,)) # TODO
    
    # Time storage
    position_update_frequency = 1 # Hz ~8km
    last_position_update_time = 0
    
    
    
    # ------------------------------------------------------------------------------------------------------------------------------------
    """ SENSOR READ FUNCTIONS """
    # ------------------------------------------------------------------------------------------------------------------------------------
    def read_sun_position(self):
        """
            - Gets the measured sun vector from light sensor measurements
            - Accesses functions inside sun.py which in turn call HAL
        """
        pass
    
    def read_gyro(self):
        """
            - Reads the angular velocity from the gyro
            - NOTE : THIS SHOULD REPLACE THE IMU TASK
        """
        pass
    
    def read_magnetometer(self):
        """
            - Reads the magnetic field reading from the IMU
            - This is separate from the gyro measurement to allow gyro to be read faster than magnetometer
        """
        pass
    
    def read_gps(self):
        """
            - Get the current position and velocity from GPS
            - NOTE: Since GPS is a task, this function will read values from C&DH
        """
        if DH.data_process_exists("gps") and SATELLITE.GPS_AVAILABLE:
            
            # Get last GPS update time
            gps_record_time = DH.get_latest_data("gps")[GPS_IDX.TIME_GPS]
            query_time = int(time.time())
            
            # If last obtained GPS measurement was within the update interval, use that position
            # NOTE: Ensure GPS position is valid before using it
            gps_pos_ecef = (np.array(DH.get_latest_data("gps")[GPS_IDX.GPS_ECEF_X : GPS_IDX.GPS_ECEF_Z + 1]).reshape((3,)) * 0.01)
            
            if not isvalid(gps_pos_ecef): # TODO : define the isvalid criterion
                
                # Update GPS based on past estimate of state
                self.state[0:3] = propagate_orbit(query_time, self.last_position_update_time, self.state[0:3])

            else:
                if abs(query_time - gps_record_time) < (1/self.position_update_frequency):
                    
                    # Use current GPS measurement without propagation
                    R_eci2ecef = ecef_to_eci(self.time)
                    self.state[0:3] = np.dot(ecef_to_eci, gps_pos_ecef)
                    
                else:
                    
                    # Propagate from GPS measurement record
                    R_eci2ecef = ecef_to_eci(self.time)
                    gps_pos_eci = np.dot(ecef_to_eci, gps_pos_ecef)
                    self.state[0:3] = propagate_orbit(query_time, gps_record_time, gps_pos_eci)
        else:
            # Update GPS based on past estimate of state
            self.state[0:3] = propagate_orbit(query_time, self.last_position_update_time, self.state[0:3])
            
        # Update last update time
        self.last_position_update_time = query_time 
            
    
    # ------------------------------------------------------------------------------------------------------------------------------------
    """ MEKF INITIALIZATION """
    # ------------------------------------------------------------------------------------------------------------------------------------
    def initialize_mekf(self):
        """
            - Initializes the MEKF using TRIAD and position from GPS
            - This function is not directly written into init to allow multiple retires of initialization
            - Sets the initialized attribute of the class once done
        """
        pass
    
    # ------------------------------------------------------------------------------------------------------------------------------------
    """ MEKF PROPAGATION """
    # ------------------------------------------------------------------------------------------------------------------------------------
    def position_update(self):
        """
            - Performs a position update
            - Accesses functions from orbit_propagation.py
            - Updates the last_position_update time attribute
            - NOTE: This is not an MEKF update. We assume that the estimated position is true
        """
        pass
    
    def sun_position_update(self):
        """
            Performs an MEKF update step for Sun position
        """
        pass
    
    def gyro_update(self):
        """
            Performs an MEKF update step for Gyro
        """
        pass
    
    def magnetometer_update(self):
        """
            Performs an MEKF update step for magnetometer
        """
        pass
    
    def update(self):
        """
            - Updates the estimated state from Attitude Determination
            - If measurements are available, it updates the 
        """
    
    
    
    