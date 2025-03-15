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
from apps.adcs.math import invert_3x3_psd
from core import logger
from hal.configuration import SATELLITE
from micropython import const
from ulab import numpy as np

MAX_RANGE = const(117000)  # OPT4001
THRESHOLD_ILLUMINATION_LUX = const(3000)
NUM_LIGHT_SENSORS = const(9)
ERROR_LUX = const(-1)


def _read_light_sensor(face):
    if SATELLITE.LIGHT_SENSOR_AVAILABLE(face):
        return SATELLITE.LIGHT_SENSORS[face].lux()
    else:
        return ERROR_LUX


def read_light_sensors():
    """
    Read the light sensors on the x+,x-,y+,y-, and z- faces of the satellite.

    Returns:
        lux_readings: list of lux readings on each face. A "ERROR_LUX" reading comes from a dysfunctional sensor.
    """

    faces = ["XP", "XM", "YP", "YM", "ZM", "ZP1", "ZP2", "ZP3", "ZP4"]
    lux_readings = []

    for face in faces:
        try:
            lux_readings.append(_read_light_sensor(face))
        except Exception as e:
            logger.warning(f"Error reading {face}: {e}")
            lux_readings.append(ERROR_LUX)

    return lux_readings


def compute_body_sun_vector_from_lux(I_vec):
    """
    Get unit sun vector expressed in the body frame from solar flux values.

    Args:
        I_vec: flux values on each face in the following order
        - X+ face, X- face, Y+ face, Y- face, Z- face, ZP1 face, ZP2 face, ZP3 face, ZP4 face

    Returns:
        sun_body: unit vector from spacecraft to sun expressed in body frame
    """

    status = None
    sun_body = np.zeros(3)

    # Determine Sun Status
    num_valid_readings = NUM_LIGHT_SENSORS - I_vec.count(ERROR_LUX)
    if num_valid_readings == 0:
        status = StatusConst.SUN_NO_READINGS
        return status, sun_body
    elif num_valid_readings < 3:

        status = StatusConst.SUN_NOT_ENOUGH_READINGS
    elif in_eclipse(I_vec, THRESHOLD_ILLUMINATION_LUX):
        status = StatusConst.SUN_ECLIPSE
        return status, sun_body
    elif num_valid_readings == 5:  # All readings are valid and unique determination is possible
        status = StatusConst.OK

    # Extract body vectors and lux readings where the sensor readings are valid
    valid_sensor_idxs = [
        idx for idx in range(len(I_vec)) if I_vec[idx] != ERROR_LUX and I_vec[idx] >= THRESHOLD_ILLUMINATION_LUX
    ]
    N_valid = PhysicalConst.LIGHT_SENSOR_NORMALS[valid_sensor_idxs, :]
    I_valid = [I_vec[idx] for idx in valid_sensor_idxs]

    # Compute the Inverse of the valid light sensor normals using the Moore-Penrose pseudo-inverse
    oprod_sun_inv = invert_3x3_psd(np.dot(N_valid.transpose(), N_valid))
    if oprod_sun_inv is None:  # If the inverse is not possible, sun positioning is not uniquely determinable
        status = StatusConst.SUN_NOT_ENOUGH_READINGS
        return status, sun_body
    else:
        oprod_sun_inv = np.dot(oprod_sun_inv, N_valid.transpose())

    # Extract the sun body vector
    sun_body = np.dot(oprod_sun_inv, I_valid)
    norm = (sun_body[0] ** 2 + sun_body[1] ** 2 + sun_body[2] ** 2) ** 0.5

    if norm == 0:  # Avoid division by zero - not perfect
        status = StatusConst.ZERO_NORM
        return status, sun_body

    sun_body = sun_body / norm

    return status, sun_body


def in_eclipse(raw_readings, threshold_lux_illumination=THRESHOLD_ILLUMINATION_LUX):
    """
    Check the eclipse conditions based on the lux readings

    Parameters:
        raw_readings (list): list of lux readings on each face (X+ face, X- face, Y+ face, Y- face, Z- face)

    Returns:
        eclipse (bool): True if the satellite is in eclipse, False if no eclipse or no correct readings.

    """
    eclipse = False

    if raw_readings.count(ERROR_LUX) == NUM_LIGHT_SENSORS:
        return eclipse

    # Check if all readings are below the threshold
    for reading in raw_readings:
        if reading != ERROR_LUX and reading >= threshold_lux_illumination:
            return eclipse

    eclipse = True

    return eclipse


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
