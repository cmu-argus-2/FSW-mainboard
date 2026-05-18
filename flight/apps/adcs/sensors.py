# from apps.adcs.consts import StatusConst
from apps.adcs.consts import ControllerConst, ControllerModes, Modes, StatusConst
from apps.adcs.sun import compute_body_sun_vector_from_lux, read_light_sensors
from hal.configuration import SATELLITE
from ulab import numpy as np

_LIGHT_SENSOR_LOG_FACTOR = 1 / 3  # scale 140k lux max down to fit 16-bit log range
_MIN_MAG_NORM = 1.0e-6  # Min allowed magnetometer reading is 1 uT (Expected field strength in orbit is ~40 uT)
_MAX_MAG_NORM = 2.5e-3  # Max allowed magnetometer reading is 2500 uT (Field strength at Mean Sea Level is ~60 uT)
# bmx160 magnetometer scale wont go past 1.3 mT in x,y and 2.5 mT in z axis
_MAX_GYRO_NORM = 2.0e3 * np.pi / 180.0  # bmx160 gyro max scale is 2000 deg/s - anything higher is likely faulty reading


def read_gyro() -> tuple[int, np.ndarray]:
    """
    - Reads the angular velocity from the gyro
    """

    if SATELLITE.IMU_AVAILABLE:
        gyro = np.array(SATELLITE.IMU.gyro())  # Gyro measurements are in rad/s

        # gyro validity check
        is_valid = True
        if gyro is None or len(gyro) != 3:
            is_valid = False
        elif not np.linalg.norm(gyro) <= _MAX_GYRO_NORM:  # Setting a very (VERY) large upper bound
            is_valid = False
        else:
            is_valid = True

        # Sensor validity check
        if not is_valid:  # is_valid_gyro_reading(gyro):
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

        # mag validity check
        is_valid = True
        if mag is None or len(mag) != 3:
            is_valid = False
        elif not (_MIN_MAG_NORM <= np.linalg.norm(mag) <= _MAX_MAG_NORM):
            is_valid = False
        else:
            is_valid = True

        # Sensor validity check
        if not is_valid:
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

    return status, sun_pos_body, np.array(light_sensor_lux_readings) * _LIGHT_SENSOR_LOG_FACTOR


def set_gyro_scale(gyro_const_value: int) -> None:
    """
    - Sets the scale configuration of the gyro
    """
    cur_gyro_scale = 0
    if SATELLITE.IMU_AVAILABLE:
        cur_gyro_scale = SATELLITE.IMU.gyro_range
    else:
        return

    if gyro_const_value != cur_gyro_scale and SATELLITE.IMU_AVAILABLE:
        SATELLITE.IMU.gyro_range = gyro_const_value


def update_mode(current_mode, ctr_mode, gyro_status, omega, sun_status, sun_pos_body) -> int:
    """
    - Returns the current mode of the ADCS
    """
    # Fail-safe STABLE mode if IMU fails
    if gyro_status != StatusConst.OK:
        return Modes.STABLE

    # Tumbling state logic - common to all controllers
    # Used to set FSW state machine to DETUMBLING
    omega_norm = np.linalg.norm(omega)

    if current_mode == Modes.TUMBLING:
        if omega_norm <= Modes.TUMBLING_TOL:
            return Modes.STABLE
        return Modes.TUMBLING
    if omega_norm >= Modes.TUMBLING_TOL:
        return Modes.TUMBLING

    # # Controller specific mode logic
    if ctr_mode != ControllerModes.SUN_POINTING:
        # # Detumbling mode - B-cross or B-dot controller
        if current_mode == Modes.STABLE:
            if omega_norm < Modes.DETUMBLED_TOL_LO:
                return Modes.ACS_OFF
            return Modes.STABLE

        # if current_mode == Modes.ACS_OFF: -> implicit
        if omega_norm >= Modes.DETUMBLED_TOL_HI:
            return Modes.STABLE
        return Modes.ACS_OFF
    # # Sun-pointing mode
    h = np.dot(ControllerConst.INERTIA_MAT, omega)
    momentum_error = np.linalg.norm(ControllerConst.INERTIA_MAJOR_DIR - (h / ControllerConst.MOMENTUM_TARGET_MAG))

    if current_mode == Modes.STABLE:
        if momentum_error <= Modes.STABLE_TOL_LO and sun_status == StatusConst.OK:
            return Modes.SUN_POINTING
        return Modes.STABLE

    if sun_status != StatusConst.OK:
        return current_mode
    h_norm = np.linalg.norm(h)
    if h_norm == 0:
        return Modes.SUN_POINTING
    sun_error = np.linalg.norm(sun_pos_body - h / h_norm)

    if current_mode == Modes.SUN_POINTING:
        if momentum_error >= Modes.STABLE_TOL_LO:
            return Modes.STABLE
        # implicit sun_status == StatusConst.OK
        if sun_error <= Modes.SUN_POINTED_TOL_LO:
            return Modes.ACS_OFF

        return Modes.SUN_POINTING

    # if current_mode == Modes.ACS_OFF: -> implicit
    if momentum_error >= Modes.STABLE_TOL_HI:
        return Modes.STABLE
    # implicit sun_status == StatusConst.OK
    if sun_error >= Modes.SUN_POINTED_TOL_HI:
        return Modes.SUN_POINTING
    return Modes.ACS_OFF
