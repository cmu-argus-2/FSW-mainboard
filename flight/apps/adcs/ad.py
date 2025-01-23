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
from apps.telemetry.constants import GPS_IDX, IMU_IDX
from apps.adcs.frames import ecef_to_eci
from apps.adcs.orbit_propagation import propagate_orbit
from apps.adcs.sun import read_light_sensors, compute_body_sun_vector_from_lux, approx_sun_position_ECI
from apps.adcs.math import skew, R_from_quat
from apps.adcs.igrf import igrf_eci

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
    
    """
        STATE DEFINITION : [position_eci (3x1), attitude_body2eci (4x1), angular_rate_body (3x1), gyro_bias (3x1), magnetic_field_body (3x1), sun_pos_body (3x1), sun_status (1x1)]
    """
    estimated_state = np.zeros((20,)) # TODO
    
    # Time storage
    position_update_frequency = 1 # Hz ~8km
    last_position_update_time = 0
    
    # EKF Covariances
    P = np.zeros((6,6))
    Q = np.zeros((6,6)) # TODO : define Q based on noise measurements
    
    # Sensor noise covariances
    sun_sensor_sigma = 0.01 # TODO : characetrize sensor and update
    magnetometer_sigma = 0.01 # TODO : characetrize sensor and update
    
    
    
    # ------------------------------------------------------------------------------------------------------------------------------------
    """ SENSOR READ FUNCTIONS """
    # ------------------------------------------------------------------------------------------------------------------------------------
    def read_sun_position(self):
        """
            - Gets the measured sun vector from light sensor measurements
            - Accesses functions inside sun.py which in turn call HAL
        """
        status, sun_pos_body = compute_body_sun_vector_from_lux(read_light_sensors())
        
        return status, sun_pos_body
        
    
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
        if SATELLITE.IMU_AVAILABLE:
                imu_mag_data = DH.get_latest_data("imu")[IMU_IDX.MAGNETOMETER_X : IMU_IDX.MAGNETOMETER_Z + 1]
                return 1, imu_mag_data
        else:
            return 0, imu_mag_data
                
    
    def read_gps(self):
        """
            - Get the current position from GPS
            - NOTE: Since GPS is a task, this function will read values from C&DH
        """
        self.time = int(time.time())
        if DH.data_process_exists("gps") and SATELLITE.GPS_AVAILABLE:
            
            # Get last GPS update time and position at that time
            gps_record_time = DH.get_latest_data("gps")[GPS_IDX.TIME_GPS]
            gps_pos_ecef = (np.array(DH.get_latest_data("gps")[GPS_IDX.GPS_ECEF_X : GPS_IDX.GPS_ECEF_Z + 1]).reshape((3,)) * 0.01)
            valid = isvalid(gps_pos_ecef) # TODO : define validity of gps signal
            
            return valid, gps_record_time, gps_pos_ecef
        else:
            return 0, 0, np.zeros((3,))
            
    
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
        gps_valid, gps_record_time, gps_pos_ecef = self.read_gps()
        
        if not gps_valid:
            # Update GPS based on past estimate of state
                self.state[0:3] = propagate_orbit(self.time, self.last_position_update_time, self.state[0:3])
        else:
            if abs(self.time - gps_record_time) < (1/self.position_update_frequency):
                    # Use current GPS measurement without propagation
                    R_ecef2eci = ecef_to_eci(self.time)
                    self.state[0:3] = np.dot(R_ecef2eci, gps_pos_ecef)
                    
            else: 
                # Propagate from GPS measurement record
                R_ecef2eci = ecef_to_eci(self.time)
                gps_pos_eci = np.dot(R_ecef2eci, gps_pos_ecef)
                self.state[0:3] = propagate_orbit(self.time, gps_record_time, gps_pos_eci)
            
        # Update last update time
        self.last_position_update_time = self.time
    
    def sun_position_update(self):
        """
            Performs an MEKF update step for Sun position
        """
        status, sun_pos_body = self.read_sun_position()
        
        self.state[-1] = status
        self.state[16:19] = sun_pos_body
        
        if status:
            true_sun_pos_eci = approx_sun_position_ECI(self.time)
            true_sun_pos_eci = true_sun_pos_eci/np.linalg.norm(true_sun_pos_eci)
            
            measured_sun_pos_eci = np.dot(R_from_quat(self.state[3:7]), sun_pos_body)
            measured_sun_pos_eci = measured_sun_pos_eci/np.linalg.norm(measured_sun_pos_eci)
            
            # EKF update
            innovation = true_sun_pos_eci - measured_sun_pos_eci
            s_cross = skew(true_sun_pos_eci)
            Cov_sunsensor = self.sun_sensor_sigma**2 * s_cross @ np.eye(3) @ s_cross.T
            
            H = np.zeros((6,6))
            H[0:3, 0:3] = -s_cross
            
            self.EKF_update(H, innovation, Cov_sunsensor)
    
    def gyro_update(self):
        """
            Performs an MEKF update step for Gyro
        """
        pass
    
    def magnetometer_update(self):
        """
            Performs an MEKF update step for magnetometer
        """
        status, mag_field_body = self.read_magnetometer()
        
        if status: # Update EKF
            
            true_mag_field_eci = igrf_eci(self.time, self.state[0:3]/1000)
            true_mag_field_eci = true_mag_field_eci/np.linalg.norm(true_mag_field_eci)
            
            measured_mag_field_eci = np.dot(R_from_quat(self.state[3:7]), mag_field_body)
            measured_mag_field_eci = measured_mag_field_eci/np.linalg.norm(measured_mag_field_eci)
            
            # EKF update
            innovation = true_mag_field_eci - measured_mag_field_eci
            s_cross = skew(true_mag_field_eci)
            Cov_mag_field = self.magnetometer_sigma**2 * s_cross @ np.eye(3) @ s_cross.T

            H = H = np.zeros((6,6))
            H[0:3, 0:3] = -s_cross
            
            self.EKF_update(H, innovation, Cov_mag_field)
             
            self.state[13:16] = mag_field_body # store magnetic field reading
            
        else: # We still need magnetic field for ACS
            # TODO : decide if we want to continue using the previous B-field or update based on position, igrf and attitude
            pass
            
    
    def EKF_update(self, H : np.ndarray, innovation : np.ndarray, R_noise : np.ndarray):
        """
            - Updates the state estimate based on available information
        """
        '''S = H @ self.P @ H.T + R_noise
        K = self.P @ H.T @ np.linalg.pinv(S, 1e-4)  # TODO tuneme
        dx = K @ innovation

        attitude_correction = R.from_rotvec(dx[:3])
        self.set_ECI_R_b(attitude_correction * self.get_ECI_R_b())

        gyro_bias_correction = dx[3:]
        self.set_gyro_bias(self.get_gyro_bias() + gyro_bias_correction)

        # Symmetric Joseph update
        Identity = np.eye(6)
        self.P = (Identity - K @ H) @ self.P @ (Identity - K @ H).T + K @ R_noise @ K.T'''
        
    
    
    
    