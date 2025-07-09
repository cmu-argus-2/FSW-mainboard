from apps.adcs.consts import ControllerConst, Modes, PhysicalConst, StatusConst
from apps.adcs.sun import compute_body_sun_vector_from_lux, read_light_sensors
from hal.configuration import SATELLITE
from ulab import numpy as np


def read_gyro() -> tuple[int, np.ndarray]:
    """
    - Reads the angular velocity from the gyro
    """

    if SATELLITE.IMU_AVAILABLE:
        gyro = np.deg2rad(np.array(SATELLITE.IMU.gyro()))  # Convert field from deg/s to rad/s

        # Sensor validity check
        if not is_valid_gyro_reading(gyro):
            return StatusConst.GYRO_FAIL, np.zeros((3,))
        else:
            return StatusConst.OK, gyro
    else:
        return StatusConst.GYRO_FAIL, np.zeros((3,))


def read_magnetometer() -> tuple[int, np.ndarray]:
    """
    - Reads the magnetic field reading from the IMU
    - This is separate from the gyro measurement to allow gyro to be read faster than magnetometer
    """

    if SATELLITE.IMU_AVAILABLE:
        mag = 1e-6 * np.array(SATELLITE.IMU.mag())  # Convert field from uT to T

        # Sensor validity check
        if not is_valid_mag_reading(mag):
            return StatusConst.MAG_FAIL, np.zeros((3,))
        else:
            return StatusConst.OK, mag

    else:
        return StatusConst.MAG_FAIL, np.zeros((3,))


def read_sun_position() -> tuple[int, np.ndarray, np.ndarray]:
    """
    - Gets the measured sun vector from light sensor measurements
    - Accesses functions inside sun.py which in turn call HAL
    """
    light_sensor_lux_readings = read_light_sensors()
    status, sun_pos_body = compute_body_sun_vector_from_lux(light_sensor_lux_readings)

    return status, sun_pos_body, np.array(light_sensor_lux_readings) / PhysicalConst.LIGHT_SENSOR_LOG_FACTOR


"""
    SENSOR VALIDITY CHECKS
"""

_MIN_MAG_NORM = 1.0e-5  # Min allowed magnetometer reading is 10 uT (Expected field strength in orbit is ~40 uT)
_MAX_MAG_NORM = 1.0e-3  # Max allowed magnetometer reading is 100 uT (Field strength at Mean Sea Level is ~60 uT)
# [TODO:] revise number above, magnetorquer might produce a strong magnetic field
_MAX_GYRO_NORM = 1.0e3  # Max allowed gyro angular velocity is 1000 deg/s (Expect to detumble at ~30 deg/s)


def is_valid_mag_reading(mag: np.ndarray) -> bool:
    # Magnetometer validity check
    if mag is None or len(mag) != 3:
        return False
    elif not (_MIN_MAG_NORM <= np.linalg.norm(mag) <= _MAX_MAG_NORM):
        return False
    else:
        return True


def is_valid_gyro_reading(gyro: np.ndarray) -> bool:
    # Gyro validity check
    if gyro is None or len(gyro) != 3:
        return False
    elif not np.linalg.norm(gyro) <= _MAX_GYRO_NORM:  # Setting a very (VERY) large upper bound
        return False
    else:
        return True


"""
    MODE DETERMINATION
"""


def current_mode(current_mode) -> int:
    """
    - Returns the current mode of the ADCS
    """
    gyro_status, omega = read_gyro()
    sun_status, sun_pos_body, _ = read_sun_position()

    # Fail-safe STABLE mode if IMU or sun acquisition fails
    # if gyro_status != StatusConst.OK or sun_status != StatusConst.OK:
    #     return Modes.STABLE

    omega_norm = np.linalg.norm(omega)

    if current_mode == Modes.TUMBLING:
        if omega_norm <= Modes.TUMBLING_TOL:
            return Modes.STABLE
        else:
            return Modes.TUMBLING

    elif current_mode == Modes.STABLE:
        if gyro_status != StatusConst.OK:
            return Modes.STABLE
        h_hat = np.dot(PhysicalConst.INERTIA_MAT, omega) / ControllerConst.MOMENTUM_TARGET_MAG
        momentum_error = np.linalg.norm(PhysicalConst.INERTIA_MAJOR_DIR - h_hat)
        if omega_norm >= Modes.TUMBLING_TOL:
            return Modes.TUMBLING

        elif momentum_error <= Modes.STABLE_TOL_LO and sun_status == StatusConst.OK:
            return Modes.SUN_POINTED

        else:
            return Modes.STABLE

    elif current_mode == Modes.SUN_POINTED:
        if gyro_status != StatusConst.OK:
            return Modes.STABLE
        h_hat = np.dot(PhysicalConst.INERTIA_MAT, omega) / ControllerConst.MOMENTUM_TARGET_MAG
        momentum_error = np.linalg.norm(PhysicalConst.INERTIA_MAJOR_DIR - h_hat)

        if momentum_error >= Modes.STABLE_TOL_LO:
            return Modes.STABLE

        if sun_status != StatusConst.OK:
            return Modes.SUN_POINTED

        sun_error = np.linalg.norm(sun_pos_body - h_hat)

        if sun_status == StatusConst.OK and sun_error <= Modes.SUN_POINTED_TOL_LO:
            return Modes.ACS_OFF

        else:
            return Modes.SUN_POINTED

    elif current_mode == Modes.ACS_OFF:
        if gyro_status != StatusConst.OK:
            return Modes.ACS_OFF
        h_hat = np.dot(PhysicalConst.INERTIA_MAT, omega) / ControllerConst.MOMENTUM_TARGET_MAG
        momentum_error = np.linalg.norm(PhysicalConst.INERTIA_MAJOR_DIR - h_hat)
        if momentum_error >= Modes.STABLE_TOL_HI:
            return Modes.STABLE
        elif sun_status == StatusConst.OK:
            sun_error = np.linalg.norm(sun_pos_body - h_hat)
            if sun_error >= Modes.SUN_POINTED_TOL_HI:
                return Modes.SUN_POINTED
            return Modes.ACS_OFF
        else:
            return Modes.ACS_OFF

    else:
        raise Exception(f"Invalid Current Mode {current_mode}")
