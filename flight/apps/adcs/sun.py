"""

Sun Acquisition Module for the Attitude Determination and Control Subsystem (ADCS).

This module is responsible for acquiring and processing light sensor data to determine the
sun vector relative to the satellite's body frame. It also determines whether the satellite
is in an eclipse based on the sensor readings.

Argus posseses 5 light sensors, 1 on each of the x+, x-, y+, y-, and z- faces of the
satellite, and a pyramid of 4 light sensors angled at 45 degrees on the z+ face.

The accuracy of the computed sun vector directly affects the performance of the ADCS system,
both for the mode transitions, sun pointing controller accuracy, and attitude determination.

"""

from apps.adcs.consts import PhysicalConst, StatusConst
from core import logger
from hal.configuration import SATELLITE
from micropython import const
from ulab import numpy as np

_MAX_RANGE = const(140000)  # OPT4001
_THRESHOLD_ILLUMINATION_LUX = const(3000)
_NUM_LIGHT_SENSORS = const(9)
_ERROR_LUX = const(-1)


def _read_light_sensor(face):
    if SATELLITE.LIGHT_SENSOR_AVAILABLE(face):
        return SATELLITE.LIGHT_SENSORS[face].lux()
    else:
        return _ERROR_LUX


def read_light_sensors():
    """
    Read the light sensors on the x+,x-,y+,y-, and z- faces of the satellite.

    Returns:
        lux_readings: list of lux readings on each face. A "ERROR_LUX" reading comes from a dysfunctional sensor.
    """

    faces = ["XP", "XM", "YP", "YM", "ZP1", "ZP2", "ZP3", "ZP4", "ZM"]
    lux_readings = []

    for face in faces:
        try:
            lux_readings.append(_read_light_sensor(face))
        except Exception as e:
            logger.warning(f"Error reading {face}: {e}")
            lux_readings.append(_ERROR_LUX)

    return lux_readings


def compute_body_sun_vector_from_lux(I_vec):
    """
    Get unit sun vector expressed in the body frame from solar flux values.

    Args:
        I_vec: flux values on each face in the following order
        - X+ face, X- face, Y+ face, Y- face, ZP1 face, ZP2 face, ZP3 face, ZP4 face, Z- face

    Returns:
        sun_body: unit vector from spacecraft to sun expressed in body frame
    """

    status = None
    sun_body = np.zeros(3)

    # Determine Sun Status
    num_valid_readings = _NUM_LIGHT_SENSORS - I_vec.count(_ERROR_LUX)
    if num_valid_readings == 0:
        status = StatusConst.SUN_NO_READINGS
        return status, sun_body
    elif num_valid_readings < 3 or missing_axis_reading(I_vec):
        status = StatusConst.SUN_NOT_ENOUGH_READINGS
        return status, sun_body
    elif in_eclipse(I_vec, _THRESHOLD_ILLUMINATION_LUX):
        status = StatusConst.SUN_ECLIPSE
        return status, sun_body
    else:
        status = StatusConst.OK

    # Extract body vectors and lux readings where the sensor readings are valid
    ACTIVE_LIGHT_READINGS = [I_vec[i] for i in range(_NUM_LIGHT_SENSORS) if I_vec[i] > _THRESHOLD_ILLUMINATION_LUX]
    ACTIVE_LIGHT_NORMALS = np.array(
        [PhysicalConst.LIGHT_SENSOR_NORMALS[i] for i in range(_NUM_LIGHT_SENSORS) if I_vec[i] > _THRESHOLD_ILLUMINATION_LUX]
    )

    # Try to perform an inverse. If the condition-number of under 1e-4, Cpy throws a ValueError for a singular matrix
    # If the pinv fails, we have a singular matrix and return a NOT_ENOUGH_READINGS flag
    try:
        sun_body = np.dot(
            np.dot(
                np.linalg.inv(np.dot(ACTIVE_LIGHT_NORMALS.transpose(), ACTIVE_LIGHT_NORMALS)), ACTIVE_LIGHT_NORMALS.transpose()
            ),
            ACTIVE_LIGHT_READINGS,
        )
    except ValueError:
        return StatusConst.SUN_NOT_ENOUGH_READINGS, sun_body

    if np.linalg.norm(sun_body) == 0:
        return StatusConst.ZERO_NORM, sun_body
    else:
        sun_body = sun_body / np.linalg.norm(sun_body)
        return StatusConst.OK, sun_body


def in_eclipse(raw_readings, threshold_lux_illumination=_THRESHOLD_ILLUMINATION_LUX):
    """
    Check the eclipse conditions based on the lux readings

    Parameters:
        raw_readings (list): list of lux readings on each face (X+ face, X- face, Y+ face, Y- face, Z- face)

    Returns:
        eclipse (bool): True if the satellite is in eclipse, False if no eclipse or no correct readings.

    """
    eclipse = False

    if raw_readings.count(_ERROR_LUX) == _NUM_LIGHT_SENSORS:
        return eclipse

    # Check if all readings are below the threshold
    for reading in raw_readings:
        if reading != _ERROR_LUX and reading >= threshold_lux_illumination:
            return eclipse

    eclipse = True

    return eclipse


def missing_axis_reading(I_vec):
    missing_x = True
    missing_y = True
    missing_z = True
    for (i, lux) in enumerate(I_vec):
        if missing_x and lux != _ERROR_LUX and i in PhysicalConst.LIGHT_X_IDXS:
            missing_x = False
        if missing_y and lux != _ERROR_LUX and i in PhysicalConst.LIGHT_Y_IDXS:
            missing_y = False
        if missing_z and lux != _ERROR_LUX and i in PhysicalConst.LIGHT_Z_IDXS:
            missing_z = False

        if not (missing_x or missing_y or missing_z):
            return False
    return True


def unix_time_to_julian_day(unix_time):
    """Takes in a unix timestamp and returns the julian day"""
    return unix_time / 86400 + 2440587.5


def approx_sun_position_ECI(utime):
    """
    Formula taken from "Satellite Orbits: Models, Methods and Applications", Section 3.3.2, page 70, by Motenbruck and Gill

    Args:
        - utime: Unix timestamp

    Returns:
        - Sun pointing in Earth Centered Intertial (ECI) frame (km)
    """
    JD = unix_time_to_julian_day(utime)
    OplusW = 282.94  # Ω + ω
    T = (JD - 2451545.0) / 36525

    M = np.radians(357.5256 + 35999.049 * T)

    long = np.radians(OplusW + np.degrees(M) + (6892 / 3600) * np.sin(M) + (72 / 3600) * np.sin(2 * M))
    r_mag = (149.619 - 2.499 * np.cos(M) - 0.021 * np.cos(2 * M)) * 10**6

    epsilon = np.radians(23.43929111)
    r_vec = np.array([r_mag * np.cos(long), r_mag * np.sin(long) * np.cos(epsilon), r_mag * np.sin(long) * np.sin(epsilon)])

    return r_vec
