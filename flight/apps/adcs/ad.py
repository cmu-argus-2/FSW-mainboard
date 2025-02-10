"""

Attitude Determination Module for the Attitude Determination and Control Subsystem (ADCS).

This module is responsible for processing GNC sensor data to determine the satellite's attitude.

Argus possesses a 3-axis IMU (Inertial Measurement Unit) providing angular rate, acceleration, and
magnetic field data on the mainboard.

"""

import time

from apps.adcs.frames import ecef_to_eci
from apps.adcs.igrf import igrf_eci
from apps.adcs.math import R_to_quat, quat_to_R, quaternion_multiply, skew
from apps.adcs.orbit_propagation import propagate_orbit
from apps.adcs.sun import SUN_VECTOR_STATUS, approx_sun_position_ECI, compute_body_sun_vector_from_lux, read_light_sensors
from apps.telemetry.constants import GPS_IDX
from core import DataHandler as DH
from core import logger
from hal.configuration import SATELLITE
from ulab import numpy as np

"""
    Attitude Determination Class
    Contains functions for the following:
        - Initializing the MEKF
        - Reading Sensors
        - Propagating MEKF
"""

STATUS_OK = 1
STATUS_FAIL = 0


class AttitudeDetermination:

    # Initialized Flag to retry initialization
    initialized = False

    """
        STATE DEFINITION : [position_eci (3x1), velocity_eci (3x1), attitude_body2eci (4x1), angular_rate_body (3x1),
                            gyro_bias (3x1), magnetic_field_body (3x1), sun_pos_body (3x1), sun_status (1x1)]
    """
    state = np.zeros((28,))  # TODO : only coded for non-pyramid light sensors
    position_idx = slice(0, 3)
    velocity_idx = slice(3, 6)
    attitude_idx = slice(6, 10)
    omega_idx = slice(10, 13)
    bias_idx = slice(13, 16)
    mag_field_idx = slice(16, 19)
    sun_pos_idx = slice(19, 22)
    sun_status_idx = slice(22, 23)
    sun_lux_idx = slice(23, 28)

    # Time storage
    position_update_frequency = 1  # Hz ~8km
    last_position_update_time = 0
    last_gyro_update_time = 0
    last_gyro_cov_update_time = 0

    # Sensor noise covariances (Decide if these numbers should be hardcoded here or placed in adcs/consts.py)
    gyro_white_noise_sigma = 0.01  # TODO : characetrize sensor and update
    gyro_bias_sigma = 0.01  # TODO : characetrize sensor and update
    sun_sensor_sigma = 0.01  # TODO : characetrize sensor and update
    magnetometer_sigma = 0.01  # TODO : characetrize sensor and update

    # EKF Covariances
    P = 10 * np.ones((6, 6))  # TODO : characterize process noise
    Q = np.eye(6)
    Q[0:3, 0:3] *= gyro_white_noise_sigma**2
    Q[3:6, 3:6] *= gyro_bias_sigma**2

    def __init__(self, id=6, task_name="ADCS"):
        self.ID = id
        self.task_name = task_name

    # ------------------------------------------------------------------------------------------------------------------------------------
    """ SENSOR READ FUNCTIONS """
    # ------------------------------------------------------------------------------------------------------------------------------------
    def read_sun_position(self) -> tuple[int, np.ndarray, np.ndarray]:
        """
        - Gets the measured sun vector from light sensor measurements
        - Accesses functions inside sun.py which in turn call HAL
        """
        light_sensor_lux_readings = read_light_sensors()
        status, sun_pos_body = compute_body_sun_vector_from_lux(light_sensor_lux_readings)

        return status, sun_pos_body, light_sensor_lux_readings

    def read_gyro(self) -> tuple[int, int, np.ndarray]:
        """
        - Reads the angular velocity from the gyro
        - NOTE : This replaces the data querying portion of the IMU task. Data logging still happens within the ADCS task
        """

        if SATELLITE.IMU_AVAILABLE:
            gyro = SATELLITE.IMU.gyro()
            query_time = int(time.time())

            return STATUS_OK, query_time, gyro
        else:
            return STATUS_FAIL, 0, np.zeros((3,))

    def read_magnetometer(self) -> tuple[int, int, np.ndarray]:
        """
        - Reads the magnetic field reading from the IMU
        - This is separate from the gyro measurement to allow gyro to be read faster than magnetometer
        """

        if SATELLITE.IMU_AVAILABLE:
            mag = SATELLITE.IMU.mag()
            query_time = int(time.time())

            return STATUS_OK, query_time, mag

        else:
            return STATUS_FAIL, 0, np.zeros((3,))

    def read_gps(self) -> tuple[int, int, np.ndarray, np.ndarray]:
        """
        - Get the current position from GPS
        - NOTE: Since GPS is a task, this function will read values from C&DH
        """
        if DH.data_process_exists("gps") and SATELLITE.GPS_AVAILABLE:

            # Get last GPS update time and position at that time
            gps_record_time = DH.get_latest_data("gps")[GPS_IDX.TIME_GPS]
            gps_pos_ecef = (
                np.array(DH.get_latest_data("gps")[GPS_IDX.GPS_ECEF_X : GPS_IDX.GPS_ECEF_Z + 1]).reshape((3,)) * 0.01
            )
            gps_vel_ecef = (
                np.array(DH.get_latest_data("gps")[GPS_IDX.GPS_ECEF_VX : GPS_IDX.GPS_ECEF_VZ + 1]).reshape((3,)) * 0.01
            )
            # TODO : define validity of gps signal

            return STATUS_OK, gps_record_time, gps_pos_ecef, gps_vel_ecef
        else:
            return STATUS_FAIL, 0, np.zeros((3,)), np.zeros((3,))

    # ------------------------------------------------------------------------------------------------------------------------------------
    """ MEKF INITIALIZATION """
    # ------------------------------------------------------------------------------------------------------------------------------------
    def initialize_mekf(self) -> int:
        """
        - Initializes the MEKF using TRIAD and position from GPS
        - This function is not directly written into init to allow multiple retires of initialization
        - Sets the initialized attribute of the class once done
        """
        # Get a valid GPS position
        gps_status, gps_record_time, gps_pos_ecef, gps_vel_ecef = self.read_gps()

        if gps_status == STATUS_FAIL:
            msg = "Failed MEKF init - GPS"
            logger.info(f"[{self.ID}][{self.task_name}] {msg}")
            return STATUS_FAIL
        else:
            # Propagate from GPS measurement record
            current_time = int(time.time())
            R_ecef2eci = ecef_to_eci(current_time)
            gps_pos_eci = np.dot(R_ecef2eci, gps_pos_ecef)
            gps_vel_eci = np.dot(R_ecef2eci, gps_vel_ecef)
            true_pos_eci, true_vel_eci = propagate_orbit(current_time, gps_record_time, gps_pos_eci, gps_vel_eci)

        # Get a valid sun position
        sun_status, sun_pos_body, lux_readings = self.read_sun_position()

        if (
            sun_status == SUN_VECTOR_STATUS.NO_READINGS
            or sun_status == SUN_VECTOR_STATUS.NOT_ENOUGH_READINGS
            or SUN_VECTOR_STATUS.ECLIPSE
        ):
            msg = "Failed MEKF init - light sensor"
            logger.info(f"[{self.ID}][{self.task_name}] {msg}")
            return STATUS_FAIL

        # Get a valid magnetometer reading
        magnetometer_status, _, mag_field_body = self.read_magnetometer()

        if magnetometer_status == STATUS_FAIL:
            msg = "Failed MEKF init - Magnetometer"
            logger.info(f"[{self.ID}][{self.task_name}] {msg}")
            return STATUS_FAIL

        # Get a gyro reading (just to store in state)
        gyro_status, _, omega_body = self.read_gyro()

        # Inertial sun position
        true_sun_pos_eci = approx_sun_position_ECI(current_time)

        # Inertial magnetic field vector
        true_mag_field_eci = igrf_eci(current_time, true_pos_eci)

        # Run TRIAD
        triad_status, attitude = self.TRIAD(true_sun_pos_eci, true_mag_field_eci, sun_pos_body, mag_field_body)

        if triad_status == STATUS_FAIL:  # If TRIAD fails, do not initialize
            return STATUS_FAIL

        self.state[self.position_idx] = true_pos_eci
        self.state[self.velocity_idx] = true_vel_eci
        self.state[self.attitude_idx] = attitude
        self.state[self.omega_idx] = omega_body
        self.state[self.bias_idx] = np.zeros((3,))
        self.state[self.mag_field_idx] = mag_field_body
        self.state[self.sun_pos_idx] = sun_pos_body
        self.state[self.sun_status_idx] = 1
        self.state[self.sun_lux_idx] = lux_readings

        self.initialized = True

        return STATUS_OK

    def TRIAD(self, n1, n2, b1, b2) -> tuple[int, np.ndarray]:
        """
        Computes the attitude of the spacecraft based on two independent vectors provided in the body and inertial frames
        """

        n1 = np.array(n1)
        n2 = np.array(n2)
        b1 = np.array(b1)
        b2 = np.array(b2)

        if np.linalg.norm(n1) == 0 or np.linalg.norm(n2) == 0 or np.linalg.norm(b1) == 0 or np.linalg.norm(b2) == 0:
            return STATUS_FAIL, np.zeros((4,))

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

        return STATUS_OK, R_to_quat(Q)

    # ------------------------------------------------------------------------------------------------------------------------------------
    """ MEKF PROPAGATION """
    # ------------------------------------------------------------------------------------------------------------------------------------
    def position_update(self, current_time: int) -> None:
        """
        - Performs a position update
        - Accesses functions from orbit_propagation.py
        - Updates the last_position_update time attribute
        - NOTE: This is not an MEKF update. We assume that the estimated position is true
        """
        gps_status, gps_record_time, gps_pos_ecef, gps_vel_ecef = self.read_gps()

        if gps_status == STATUS_FAIL:
            # Update GPS based on past estimate of state
            self.state[self.position_idx], self.state[self.velocity_idx] = propagate_orbit(
                current_time, self.last_position_update_time, self.state[self.position_idx], self.state[self.velocity_idx]
            )
        else:
            if abs(current_time - gps_record_time) < (1 / self.position_update_frequency):
                # Use current GPS measurement without propagation
                R_ecef2eci = ecef_to_eci(current_time)
                self.state[self.position_idx] = np.dot(R_ecef2eci, gps_pos_ecef)
                self.state[self.velocity_idx] = np.dot(R_ecef2eci, gps_vel_ecef)

            else:
                # Propagate from GPS measurement record
                R_ecef2eci = ecef_to_eci(current_time)
                gps_pos_eci = np.dot(R_ecef2eci, gps_pos_ecef)
                gps_vel_eci = np.dot(R_ecef2eci, gps_vel_ecef)
                self.state[self.position_idx], self.state[self.velocity_idx] = propagate_orbit(
                    current_time, gps_record_time, gps_pos_eci, gps_vel_eci
                )

        # Update last update time
        self.last_position_update_time = current_time

    def sun_position_update(self, current_time: int, update_covariance: bool = True) -> None:
        """
        Performs an MEKF update step for Sun position
        """

        status, sun_pos_body, lux_readings = self.read_sun_position()

        self.state[self.sun_status_idx] = status
        self.state[self.sun_pos_idx] = sun_pos_body
        self.state[self.sun_lux_idx] = lux_readings

        if (
            self.initialized
            and update_covariance
            and status not in [SUN_VECTOR_STATUS.NO_READINGS, SUN_VECTOR_STATUS.NOT_ENOUGH_READINGS, SUN_VECTOR_STATUS.ECLIPSE]
        ):
            true_sun_pos_eci = approx_sun_position_ECI(current_time)
            true_sun_pos_eci_norm = np.linalg.norm(true_sun_pos_eci)
            if true_sun_pos_eci_norm == 0:
                return  # End update if true position is absent
            else:
                true_sun_pos_eci = true_sun_pos_eci / true_sun_pos_eci_norm

            measured_sun_pos_eci = np.dot(quat_to_R(self.state[self.attitude_idx]), sun_pos_body)
            measured_sun_pos_eci_norm = np.linalg.norm(measured_sun_pos_eci)
            if measured_sun_pos_eci_norm == 0:
                return  # End update if measured position is absent
            else:
                measured_sun_pos_eci = measured_sun_pos_eci / measured_sun_pos_eci_norm

            # EKF update
            innovation = true_sun_pos_eci - measured_sun_pos_eci
            s_cross = skew(true_sun_pos_eci)
            Cov_sunsensor = self.sun_sensor_sigma**2 * np.dot(np.dot(s_cross, np.eye(3)), s_cross.transpose())
            H = np.zeros((3, 6))
            H[0:3, 0:3] = -s_cross

            self.EKF_update(H, innovation, Cov_sunsensor)

    def gyro_update(self, current_time: int, update_covariance: bool = True) -> None:
        """
        Performs an MEKF update step for Gyro
        If update_error_covariance is False, the gyro measurements just update the attitude
        but do not reduce uncertainity in error measurements
        """
        status, _, omega_body = self.read_gyro()

        self.state[self.omega_idx] = omega_body  # save omega to state

        if status == STATUS_OK:

            if self.initialized:  # If initialized, also update attitude via propagation
                bias = self.state[self.bias_idx]
                dt = current_time - self.last_gyro_update_time

                unbiased_omega = omega_body - bias
                rotvec = unbiased_omega * dt
                rotvec_norm = np.linalg.norm(rotvec)
                if rotvec_norm == 0:
                    delta_quat = np.array([1, 0, 0, 0])  # Unit quaternion
                else:
                    delta_quat = np.zeros((4,))
                    delta_quat[0] = np.cos(rotvec_norm / 2)
                    delta_quat[1:4] = np.sin(rotvec_norm / 2) * rotvec / rotvec_norm

                self.state[self.attitude_idx] = quaternion_multiply(self.state[self.attitude_idx], delta_quat)
                R_q_next = quat_to_R(self.state[self.attitude_idx])

                self.last_gyro_update_time = current_time

                if update_covariance:  # if update covariance, update covariance matrices

                    F = np.zeros((6, 6))
                    F[0:3, 3:6] = -R_q_next

                    G = np.zeros((6, 6))
                    G[0:3, 0:3] = -R_q_next
                    G[3:6, 3:6] = np.eye(3)

                    A = np.zeros((12, 12))
                    A[0:6, 0:6] = F
                    A[0:6, 6:12] = np.dot(np.dot(G, self.Q), G.transpose())
                    A[6:12, 6:12] = F.transpose()
                    A = A * dt

                    Aexp = np.eye(12) + A
                    Phi = Aexp[6:12, 6:12].transpose()
                    Qdk = np.dot(Phi, Aexp[0:6, 6:12])
                    Qdk = np.dot(np.dot(Phi, self.P), Phi.transpose()) + Qdk
                    self.P = np.dot(np.dot(Phi, self.P), Phi.transpose()) + Qdk

    def magnetometer_update(self, current_time=int, update_covariance: bool = True) -> None:
        """
        Performs an MEKF update step for magnetometer
        """

        status, _, mag_field_body = self.read_magnetometer()

        if self.initialized and update_covariance and status == STATUS_OK:  # Update EKF

            true_mag_field_eci = igrf_eci(current_time, self.state[self.position_idx] / 1000)
            true_mag_field_eci_norm = np.linalg.norm(true_mag_field_eci)
            if true_mag_field_eci_norm == 0:
                return  # End update if true mag field is zeros
            else:
                true_mag_field_eci = true_mag_field_eci / true_mag_field_eci_norm

            measured_mag_field_eci = np.dot(quat_to_R(self.state[self.attitude_idx]), mag_field_body)
            measured_mag_field_eci_norm = np.linalg.norm(measured_mag_field_eci)
            if measured_mag_field_eci_norm == 0:
                return  # End update if measured mag field is zeros
            else:
                measured_mag_field_eci = measured_mag_field_eci / measured_mag_field_eci_norm

            # EKF update
            innovation = true_mag_field_eci - measured_mag_field_eci
            s_cross = skew(true_mag_field_eci)
            Cov_mag_field = self.magnetometer_sigma**2 * np.dot(np.dot(s_cross, np.eye(3)), s_cross.transpose())
            H = np.zeros((3, 6))
            H[0:3, 0:3] = -s_cross

            self.EKF_update(H, innovation, Cov_mag_field)

        if status == STATUS_OK:
            self.state[self.mag_field_idx] = mag_field_body  # store magnetic field reading

    def EKF_update(self, H: np.ndarray, innovation: np.ndarray, R_noise: np.ndarray) -> None:
        """
        - Updates the state estimate based on available information
        """
        S = np.dot(np.dot(H, self.P), H.transpose()) + R_noise

        # ulab inv declares a matrix singular if det < 5E-2
        # S is scaled up by 1000 and then down to remove this error
        # If the singularity persists, we stop the covariance update
        try:
            S_inv = 1000 * np.linalg.inv(1000 * S)
        except ValueError:
            msg = "Singular Matrix : Stopping covariance update"
            logger.info(f"[{self.ID}][{self.task_name}] {msg}")
            return
        K = np.dot(np.dot(self.P, H.transpose()), S_inv)
        dx = np.dot(K, innovation)

        dq_norm = np.linalg.norm(dx[0:3])
        if dq_norm == 0:
            attitude_correction = np.array([1, 0, 0, 0])  # Unit quaternion
        else:
            attitude_correction = np.zeros((4,))
            attitude_correction[0] = np.cos(dq_norm / 2)
            attitude_correction[1:4] = np.sin(dq_norm / 2) * dx[0:3] / dq_norm

        self.state[self.attitude_idx] = quaternion_multiply(self.state[self.attitude_idx], attitude_correction)

        gyro_bias_correction = dx[3:]
        self.state[self.bias_idx] = self.state[self.bias_idx] + gyro_bias_correction

        # Symmetric Joseph update
        Identity = np.eye(6)
        self.P = np.dot(np.dot((Identity - np.dot(K, H)), self.P), (Identity - np.dot(K, H)).transpose()) + np.dot(
            np.dot(K, R_noise), K.transpose()
        )
