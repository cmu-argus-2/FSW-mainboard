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

from core import logger
from hal.configuration import SATELLITE
from micropython import const
from ulab import numpy as np

MAX_RANGE = const(117000)  # OPT4001
THRESHOLD_ILLUMINATION_LUX = const(3000)
NUM_LIGHT_SENSORS = const(5)
ERROR_LUX = const(-1)


class SUN_VECTOR_STATUS:
    UNIQUE_DETERMINATION = 0x0  # Successful computation with at least 3 lux readings
    UNDETERMINED_VECTOR = 0x1  # Vector computed with less than 3 lux readings
    NOT_ENOUGH_READINGS = 0x2  # Computation failed due to lack of readings (less than 3 valid readings)
    NO_READINGS = 0x3
    MISSING_XP_READING = 0x4
    MISSING_XM_READING = 0x5
    MISSING_YP_READING = 0x6
    MISSING_YM_READING = 0x7
    MISSING_ZM_READING = 0x8
    MISSING_FULL_X_AXIS_READING = 0x9
    MISSING_FULL_Y_AXIS_READING = 0xA
    MISSING_FULL_Z_AXIS_READING = 0xB


def _read_light_sensor(face):
    if SATELLITE.LIGHT_SENSORS[face] is not None:
        return SATELLITE.LIGHT_SENSORS[face].lux()
    else:
        return ERROR_LUX


def read_light_sensors():
    """
    Read the light sensors on the x+,x-,y+,y-, and z- faces of the satellite.

    Returns:
        lux_readings: list of lux readings on each face. A "ERROR_LUX" reading comes from a dysfunctional sensor.
    """

    faces = ["XP", "XM", "YP", "YM", "ZM"]
    lux_readings = []

    for face in faces:
        try:
            lux_readings.append(_read_light_sensor(face))
        except Exception as e:
            logger.warning(f"Error reading {face}: {e}")
            lux_readings.append(ERROR_LUX)

    # Placeholder for the z+ face pyramid reading
    # lux_readings.append(ERROR_LUX)

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

    N = np.array(
        [
            [1, 0, 0],
            [-1, 0, 0],
            [0, 1, 0],
            [0, -1, 0],
            [0.7071, 0, 0.7071],
            [0, 0.7071, 0.7071],
            [-0.7071, 0, 0.7071],
            [0, -0.7071, 0.7071],
        ]
    )  # map from light sensors to body vector

    num_valid_readings = NUM_LIGHT_SENSORS - I_vec.count(ERROR_LUX)

    if num_valid_readings == 0:
        status = SUN_VECTOR_STATUS.NO_READINGS
        return status, sun_body
    elif num_valid_readings < 3:
        status = SUN_VECTOR_STATUS.NOT_ENOUGH_READINGS
    elif num_valid_readings >= 3:  # All readings are valid and unique determination is possible
        status = SUN_VECTOR_STATUS.UNIQUE_DETERMINATION

    valid_sensor_idxs = np.where(I_vec == ERROR_LUX)[0]

    # Extract body vectors and lux readings where the sensor readings are valid
    N_valid = N[valid_sensor_idxs, :]
    I_valid = I_vec[valid_sensor_idxs]

    # Extract the sun body vector
    # NOTE : ulab does not have a pinv operation
    # Using the Moore-Penrose psuedo-inverse
    sun_body = np.linalg.inv(N_valid.transpose() @ N_valid) @ N_valid.transpose() @ I_valid

    norm = (sun_body[0] ** 2 + sun_body[1] ** 2 + sun_body[2] ** 2) ** 0.5

    if norm == 0:  # Avoid division by zero - not perfect
        status = SUN_VECTOR_STATUS.UNDETERMINED_VECTOR
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


def read_pyramid_sun_sensor_zm():
    # TODO
    pass


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
