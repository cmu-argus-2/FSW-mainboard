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


def read_deployment_sensors(sens_id) -> float:
    """
    - Reads the deployment sensor distances from HAL
    - Returns the distance for XP or YM sensors
    """
    return SATELLITE.DEPLOYMENT_SENSOR_DISTANCE(sens_id)


def get_gyro_scale() -> int:
    """
    - Reads the scale configuration of the gyro
    """

    if SATELLITE.IMU_AVAILABLE:
        return SATELLITE.IMU.gyro_range
    else:
        return StatusConst.GYRO_FAIL


def set_gyro_scale(gyro_const_value: int) -> None:
    """
    - Sets the scale configuration of the gyro
    """

    if SATELLITE.IMU_AVAILABLE:
        SATELLITE.IMU.gyro_range = gyro_const_value


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
