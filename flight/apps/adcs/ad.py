"""

Attitude Determination Module for the Attitude Determination and Control Subsystem (ADCS).

This module is responsible for processing GNC sensor data to determine the satellite's attitude.

Argus possesses a 3-axis IMU (Inertial Measurement Unit) providing angular rate, acceleration, and
magnetic field data on the mainboard.

"""

from apps.adcs.consts import ControllerConst, Modes, PhysicalConst, StatusConst
from apps.adcs.igrf import igrf_eci
from apps.adcs.math import R_to_quat, quat_to_R, quaternion_multiply, skew
from apps.adcs.orbit_propagation import OrbitPropagator
from apps.adcs.sun import approx_sun_position_ECI, compute_body_sun_vector_from_lux, read_light_sensors
from apps.adcs.utils import is_valid_gyro_reading, is_valid_mag_reading
from core.time_processor import TimeProcessor as TPM
from hal.configuration import SATELLITE
from ulab import numpy as np

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
        STATE DEFINITION : [position_eci (3x1), velocity_eci (3x1), attitude_body2eci (4x1), angular_rate_body (3x1),
                            gyro_bias (3x1), magnetic_field_body (3x1), sun_pos_body (3x1), sun_status (1x1)]
    """
    state = np.zeros((32,))
    position_idx = slice(0, 3)
    velocity_idx = slice(3, 6)
    attitude_idx = slice(6, 10)
    omega_idx = slice(10, 13)
    bias_idx = slice(13, 16)
    mag_field_idx = slice(16, 19)
    sun_pos_idx = slice(19, 22)
    sun_status_idx = slice(22, 23)
    sun_lux_idx = slice(23, 32)

    true_map = np.zeros((6,))

    # Time storage
    last_gyro_update_time = 0
    mekf_init_start_time = None
    mekf_timeout = 300  # seconds TODO: Decide a timeout and change

    # Sensor noise covariances (Decide if these numbers should be hardcoded here or placed in adcs/consts.py)
    gyro_white_noise_sigma = 1.5e-4  # TODO : characetrize sensor and update
    gyro_bias_sigma = 1.5e-4  # TODO : characetrize sensor and update
    sun_sensor_sigma = 1e-4  # TODO : characetrize sensor and update
    magnetometer_sigma = 3e-1  # TODO : characetrize sensor and update

    # EKF Covariances
    P = 10 * np.ones((6, 6))  # TODO : characterize process noise
    Q = np.eye(6)
    Q[0:3, 0:3] *= gyro_white_noise_sigma**2
    Q[3:6, 3:6] *= gyro_bias_sigma**2

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

        return status, sun_pos_body, np.array(light_sensor_lux_readings) / PhysicalConst.LIGHT_SENSOR_LOG_FACTOR

    def read_gyro(self) -> tuple[int, int, np.ndarray]:
        """
        - Reads the angular velocity from the gyro
        - NOTE : This replaces the data querying portion of the IMU task. Data logging still happens within the ADCS task
        """

        if SATELLITE.IMU_AVAILABLE:
            gyro = np.deg2rad(np.array(SATELLITE.IMU.gyro()))  # Convert gyro reading from deg/s to rad/s
            query_time = TPM.time()

            # Sensor validity check
            if not is_valid_gyro_reading(gyro):
                return StatusConst.GYRO_FAIL, 0, np.zeros((3,))
            else:
                return StatusConst.OK, query_time, gyro
        else:
            return StatusConst.GYRO_FAIL, 0, np.zeros((3,))

    def read_magnetometer(self) -> tuple[int, int, np.ndarray]:
        """
        - Reads the magnetic field reading from the IMU
        - This is separate from the gyro measurement to allow gyro to be read faster than magnetometer
        """

        if SATELLITE.IMU_AVAILABLE:
            mag = 1e-6 * np.array(SATELLITE.IMU.mag())  # Convert field from uT to T

            query_time = TPM.time()

            # Sensor validity check
            if not is_valid_mag_reading(mag):
                return StatusConst.MAG_FAIL, 0, np.zeros((3,))
            else:
                return StatusConst.OK, query_time, mag

        else:
            return StatusConst.MAG_FAIL, 0, np.zeros((3,))

    # ------------------------------------------------------------------------------------------------------------------------------------
    """ MEKF INITIALIZATION """

    # ------------------------------------------------------------------------------------------------------------------------------------
    def initialize_mekf(self) -> int:
        """
        - Initializes the MEKF using TRIAD and position from GPS
        - This function is not directly written into init to allow multiple retires of initialization
        - Sets the initialized attribute of the class once done
        """
        current_time = TPM.time()

        if self.mekf_init_start_time is None:
            self.mekf_init_start_time = current_time
        elif abs(current_time - self.mekf_init_start_time) >= self.mekf_timeout:
            # Ignore MEKF initialization
            self.state[self.attitude_idx] = np.array([1, 0, 0, 0])
            self.initialized = True
            self.last_gyro_update_time = current_time
            return StatusConst.OK, StatusConst.MEKF_INIT_FORCE

        # Get a valid position from OrbitProp
        # status, true_pos_eci, true_vel_eci = OrbitPropagator.update_position(current_time)

        # if status != StatusConst.OK:
        #     return StatusConst.MEKF_INIT_FAIL, status

        # Get a valid sun position
        sun_status, sun_pos_body, lux_readings = self.read_sun_position()

        if (
            sun_status == StatusConst.SUN_NO_READINGS
            or sun_status == StatusConst.SUN_NOT_ENOUGH_READINGS
            or sun_status == StatusConst.SUN_ECLIPSE
        ):
            return StatusConst.MEKF_INIT_FAIL, sun_status

        # Get a valid magnetometer reading
        magnetometer_status, _, mag_field_body = self.read_magnetometer()

        if magnetometer_status == StatusConst.MAG_FAIL:
            return StatusConst.MEKF_INIT_FAIL, StatusConst.MAG_FAIL

        # Get a gyro reading (just to store in state)
        _, _, omega_body = self.read_gyro()

        # Inertial sun position
        # true_sun_pos_eci = approx_sun_position_ECI(current_time)

        # Inertial magnetic field vector
        # true_mag_field_eci = igrf_eci(current_time, true_pos_eci)

        # Run TRIAD
        # triad_status, attitude = self.TRIAD(true_sun_pos_eci, true_mag_field_eci, sun_pos_body, mag_field_body)

        # if triad_status == StatusConst.TRIAD_FAIL:  # If TRIAD fails, do not initialize
        #     return StatusConst.MEKF_INIT_FAIL, StatusConst.TRIAD_FAIL

        # Log variables to state
        self.state[self.position_idx] = np.zeros((3,))  # true_pos_eci
        self.state[self.velocity_idx] = np.zeros((3,))  # true_vel_eci
        self.state[self.attitude_idx] = np.zeros((4,))  # attitude
        self.state[self.omega_idx] = omega_body
        self.state[self.bias_idx] = np.zeros((3,))
        self.state[self.mag_field_idx] = mag_field_body
        self.state[self.sun_pos_idx] = sun_pos_body
        self.state[self.sun_status_idx] = 1
        self.state[self.sun_lux_idx] = lux_readings

        self.initialized = True
        self.last_gyro_update_time = current_time

        return StatusConst.OK, StatusConst.OK

    def TRIAD(self, n1, n2, b1, b2) -> tuple[int, np.ndarray]:
        """
        Computes the attitude of the spacecraft based on two independent vectors provided in the body and inertial frames
        """

        n1 = np.array(n1)
        n2 = np.array(n2)
        b1 = np.array(b1)
        b2 = np.array(b2)

        if np.linalg.norm(n1) == 0 or np.linalg.norm(n2) == 0 or np.linalg.norm(b1) == 0 or np.linalg.norm(b2) == 0:
            return StatusConst.TRIAD_FAIL, np.zeros((4,))

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

        return StatusConst.OK, R_to_quat(Q)

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

        # Get a valid position from OrbitProp
        status, true_pos_eci, true_vel_eci = OrbitPropagator.update_position(current_time)

        if status != StatusConst.OK:
            return StatusConst.POS_UPDATE_FAIL, status
        else:
            self.state[self.position_idx] = true_pos_eci
            self.state[self.velocity_idx] = true_vel_eci

        return StatusConst.OK, StatusConst.OK

    def sun_position_update(self, current_time: int) -> None:
        """
        Performs an MEKF update step for Sun position
        """

        status, sun_pos_body, lux_readings = self.read_sun_position()

        self.state[self.sun_status_idx] = status
        self.state[self.sun_pos_idx] = sun_pos_body
        self.state[self.sun_lux_idx] = lux_readings

        return StatusConst.OK, status

    def magnetometer_update(self, current_time=int) -> None:
        """
        Performs an MEKF update step for magnetometer
        """

        status, _, mag_field_body = self.read_magnetometer()

        if status == StatusConst.OK:  # store magnetic field reading even if update fails to use for ACS
            self.state[self.mag_field_idx] = mag_field_body

        # Perform an update only if MEKF initialized and valid field reading obtained
        return StatusConst.OK, status

    def gyro_update(self, current_time: int) -> None:
        """
        Performs an MEKF update step for Gyro
        If update_error_covariance is False, the gyro measurements just update the attitude
        but do not reduce uncertainity in error measurements
        """
        status, _, omega_body = self.read_gyro()

        self.state[self.omega_idx] = omega_body  # save omega to state

        if status == StatusConst.OK:
            """
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
            """
            self.last_gyro_update_time = current_time

    def current_mode(self, current_mode) -> int:
        """
        - Returns the current mode of the ADCS
        """
        omega = np.linalg.norm(self.state[self.omega_idx])
        if current_mode == Modes.TUMBLING:
            if omega <= Modes.TUMBLING_TOL:
                return Modes.STABLE
            else:
                return Modes.TUMBLING
        elif current_mode == Modes.STABLE:
            momentum_error = np.linalg.norm(
                PhysicalConst.INERTIA_MAJOR_DIR
                - np.dot(PhysicalConst.INERTIA_MAT, self.state[self.omega_idx]) / ControllerConst.MOMENTUM_TARGET_MAG
            )
            # ControllerConst.MOMENTUM_TARGET - np.dot(PhysicalConst.INERTIA_MAT, self.state[self.omega_idx])

            if omega >= Modes.TUMBLING_TOL:
                return Modes.TUMBLING

            elif momentum_error <= Modes.STABLE_TOL_LO:
                return Modes.SUN_POINTED

            else:
                return Modes.STABLE

        elif current_mode == Modes.SUN_POINTED:
            momentum_error = np.linalg.norm(
                PhysicalConst.INERTIA_MAJOR_DIR
                - np.dot(PhysicalConst.INERTIA_MAT, self.state[self.omega_idx]) / ControllerConst.MOMENTUM_TARGET_MAG
            )
            # ControllerConst.MOMENTUM_TARGET - np.dot(PhysicalConst.INERTIA_MAT, self.state[self.omega_idx])

            sun_error = np.linalg.norm(
                self.state[self.sun_pos_idx]
                - np.dot(PhysicalConst.INERTIA_MAT, self.state[self.omega_idx])
                / np.linalg.norm(ControllerConst.MOMENTUM_TARGET)
            )

            if momentum_error >= Modes.STABLE_TOL_LO:
                return Modes.STABLE

            elif self.state[self.sun_status_idx] == StatusConst.OK and sun_error <= Modes.SUN_POINTED_TOL_LO:
                return Modes.ACS_OFF

            else:
                return Modes.SUN_POINTED

        elif current_mode == Modes.ACS_OFF:
            momentum_error = np.linalg.norm(
                PhysicalConst.INERTIA_MAJOR_DIR
                - np.dot(PhysicalConst.INERTIA_MAT, self.state[self.omega_idx]) / ControllerConst.MOMENTUM_TARGET_MAG
            )
            # ControllerConst.MOMENTUM_TARGET - np.dot(PhysicalConst.INERTIA_MAT, self.state[self.omega_idx])
            if momentum_error >= Modes.STABLE_TOL_HI:
                return Modes.STABLE

            if self.state[self.sun_status_idx] == StatusConst.OK:
                sun_error = np.linalg.norm(
                    self.state[self.sun_pos_idx]
                    - np.dot(PhysicalConst.INERTIA_MAT, self.state[self.omega_idx])
                    / np.linalg.norm(ControllerConst.MOMENTUM_TARGET)
                )
                if sun_error >= Modes.SUN_POINTED_TOL_HI:
                    return Modes.SUN_POINTED
                return Modes.ACS_OFF
            else:
                return Modes.ACS_OFF

        else:
            raise Exception(f"Invalid Current Mode {current_mode}")
