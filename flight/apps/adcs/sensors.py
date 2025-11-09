from apps.adcs.consts import ControllerConst, Modes, StatusConst, SunConst
from apps.adcs.sun import compute_body_sun_vector_from_lux, read_light_sensors
from hal.configuration import SATELLITE
from ulab import numpy as np


def read_gyro() -> tuple[int, np.ndarray]:
    """
    - Reads the angular velocity from the gyro
    """

    if SATELLITE.IMU_AVAILABLE:
        gyro = np.array(SATELLITE.IMU.gyro())  # Gyro measurements are in rad/s

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

    return status, sun_pos_body, np.array(light_sensor_lux_readings) / SunConst.LIGHT_SENSOR_LOG_FACTOR


def read_deployment_sensors(sens_id) -> tuple[float, float]:
    """
    - Reads the deployment sensor distances from HAL
    - Returns the distance for XP or YM sensors
    """
    return SATELLITE.DEPLOYMENT_SENSOR_DISTANCE(sens_id)


"""
    SENSOR VALIDITY CHECKS
"""

_MIN_MAG_NORM = 1.0e-6  # Min allowed magnetometer reading is 1 uT (Expected field strength in orbit is ~40 uT)
_MAX_MAG_NORM = 2.5e-3  # Max allowed magnetometer reading is 2500 uT (Field strength at Mean Sea Level is ~60 uT)
# bmx160 magnetometer scale wont go past 1.3 mT in x,y and 2.5 mT in z axis
_MAX_GYRO_NORM = 2.0e3 * np.pi / 180.0  # bmx160 gyro max scale is 2000 deg/s - anything higher is likely faulty reading


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


def current_mode(current_mode, ctr_const: ControllerConst) -> int:
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
        h_hat = np.dot(ctr_const.INERTIA_MAT, omega) / ctr_const.MOMENTUM_TARGET_MAG
        momentum_error = np.linalg.norm(ctr_const.INERTIA_MAJOR_DIR - h_hat)
        if omega_norm >= Modes.TUMBLING_TOL:
            return Modes.TUMBLING

        elif momentum_error <= Modes.STABLE_TOL_LO and sun_status == StatusConst.OK:
            return Modes.SUN_POINTED

        else:
            return Modes.STABLE

    elif current_mode == Modes.SUN_POINTED:
        if gyro_status != StatusConst.OK:
            return Modes.STABLE
        h_hat = np.dot(ctr_const.INERTIA_MAT, omega) / ctr_const.MOMENTUM_TARGET_MAG
        momentum_error = np.linalg.norm(ctr_const.INERTIA_MAJOR_DIR - h_hat)

        if momentum_error >= Modes.STABLE_TOL_LO:
            return Modes.STABLE

        if sun_status != StatusConst.OK:
            return Modes.SUN_POINTED

        h = np.dot(ctr_const.INERTIA_MAT, omega)
        h_hat = h / np.linalg.norm(h)  # conical condition
        sun_error = np.linalg.norm(sun_pos_body - h_hat)

        if sun_status == StatusConst.OK and sun_error <= Modes.SUN_POINTED_TOL_LO:
            return Modes.ACS_OFF

        else:
            return Modes.SUN_POINTED

    elif current_mode == Modes.ACS_OFF:
        if gyro_status != StatusConst.OK:
            return Modes.ACS_OFF
        h_hat = np.dot(ctr_const.INERTIA_MAT, omega) / ctr_const.MOMENTUM_TARGET_MAG
        momentum_error = np.linalg.norm(ctr_const.INERTIA_MAJOR_DIR - h_hat)
        if momentum_error >= Modes.STABLE_TOL_HI:
            return Modes.STABLE
        elif sun_status == StatusConst.OK:
            h = np.dot(ctr_const.INERTIA_MAT, omega)
            h_hat = h / np.linalg.norm(h)  # conical condition
            sun_error = np.linalg.norm(sun_pos_body - h_hat)
            if sun_error >= Modes.SUN_POINTED_TOL_HI:
                return Modes.SUN_POINTED
            return Modes.ACS_OFF
        else:
            return Modes.ACS_OFF

    else:
        raise Exception(f"Invalid Current Mode {current_mode}")
