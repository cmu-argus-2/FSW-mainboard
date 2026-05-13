import os
import struct

from apps.adcs.consts import StatusConst, SunConst
from apps.adcs.sun import compute_body_sun_vector_from_lux, read_light_sensors
from hal.configuration import SATELLITE
from ulab import numpy as np

_CAL_PATH = "/sd/config/sensor_cal.bin"
_CAL_FMT = "9f"
_sensor_cal_loaded = False

_GYRO_BIAS = np.zeros(3)
_MAG_BIAS = np.zeros(3)
_MAG_SCALE = np.ones(3)


def load_sensor_cal():
    global _sensor_cal_loaded
    if _sensor_cal_loaded:
        return
    _sensor_cal_loaded = True
    try:
        with open(_CAL_PATH, "rb") as f:
            vals = struct.unpack(_CAL_FMT, f.read(struct.calcsize(_CAL_FMT)))
        _GYRO_BIAS[0] = vals[0]
        _GYRO_BIAS[1] = vals[1]
        _GYRO_BIAS[2] = vals[2]
        _MAG_BIAS[0] = vals[3]
        _MAG_BIAS[1] = vals[4]
        _MAG_BIAS[2] = vals[5]
        _MAG_SCALE[0] = vals[6]
        _MAG_SCALE[1] = vals[7]
        _MAG_SCALE[2] = vals[8]
    except Exception:
        pass


def _save_sensor_cal():
    try:
        with open(_CAL_PATH, "wb") as f:
            f.write(
                struct.pack(
                    _CAL_FMT,
                    _GYRO_BIAS[0],
                    _GYRO_BIAS[1],
                    _GYRO_BIAS[2],
                    _MAG_BIAS[0],
                    _MAG_BIAS[1],
                    _MAG_BIAS[2],
                    _MAG_SCALE[0],
                    _MAG_SCALE[1],
                    _MAG_SCALE[2],
                )
            )
        os.sync()
    except Exception:
        pass


def update_gyro_bias(b_x, b_y, b_z):
    _GYRO_BIAS[0] = b_x
    _GYRO_BIAS[1] = b_y
    _GYRO_BIAS[2] = b_z
    _save_sensor_cal()


def update_mag_cal(b_x, b_y, b_z, s_x, s_y, s_z):
    _MAG_BIAS[0] = b_x
    _MAG_BIAS[1] = b_y
    _MAG_BIAS[2] = b_z
    _MAG_SCALE[0] = s_x
    _MAG_SCALE[1] = s_y
    _MAG_SCALE[2] = s_z
    _save_sensor_cal()


def read_gyro() -> tuple[int, np.ndarray]:
    """
    - Reads the angular velocity from the gyro
    """

    if SATELLITE.IMU_AVAILABLE:
        gyro = np.array(SATELLITE.IMU.gyro())  # Gyro measurements are in rad/s
        gyro -= _GYRO_BIAS

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
        mag -= _MAG_BIAS
        mag *= _MAG_SCALE

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

    return status, sun_pos_body, np.array(light_sensor_lux_readings) * SunConst.LIGHT_SENSOR_LOG_FACTOR


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
