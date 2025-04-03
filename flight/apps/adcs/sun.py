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

ACTIVE_LIGHT_SENSORS = np.ones((_NUM_LIGHT_SENSORS,))


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

    faces = ["XP", "XM", "YP", "YM", "ZM", "ZP1", "ZP2", "ZP3", "ZP4"]
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
    elif num_valid_readings < 3:
        status = StatusConst.SUN_NOT_ENOUGH_READINGS
    elif in_eclipse(I_vec, _THRESHOLD_ILLUMINATION_LUX):
        status = StatusConst.SUN_ECLIPSE
        return status, sun_body
    else:
        status = StatusConst.OK

    # Extract body vectors and lux readings where the sensor readings are valid
    ACTIVE_LIGHT_SENSORS = np.array(I_vec) > _THRESHOLD_ILLUMINATION_LUX

    # X sun position (initial estimate)
    if I_vec[0] > I_vec[1]:
        if ACTIVE_LIGHT_SENSORS[0]:
            sun_body[0] = I_vec[0] / PhysicalConst.LIGHT_SENSOR_NORMALS[0, 0]
        else:
            sun_body[0] = 0
    else:
        if ACTIVE_LIGHT_SENSORS[1]:
            sun_body[0] = I_vec[1] / PhysicalConst.LIGHT_SENSOR_NORMALS[1, 0]
        else:
            sun_body[0] = 0

    # Y sun position (initial estimate)
    if I_vec[2] > I_vec[3]:
        if ACTIVE_LIGHT_SENSORS[2]:
            sun_body[1] = I_vec[2] / PhysicalConst.LIGHT_SENSOR_NORMALS[2, 1]
        else:
            sun_body[1] = 0
    else:
        if ACTIVE_LIGHT_SENSORS[3]:
            sun_body[1] = I_vec[3] / PhysicalConst.LIGHT_SENSOR_NORMALS[3, 1]
        else:
            sun_body[1] = 0

    # Z position (initial estimate)
    sun_body[2] = I_vec[8] / PhysicalConst.LIGHT_SENSOR_NORMALS[8, 2] if ACTIVE_LIGHT_SENSORS[8] else 0

    # Refine Estimates
    if sun_body[2] != 0:  # Sun illuminates the ZM face
        if sun_body[0] == 0:  # XP / XM faces are dead
            sun_body[0] = (
                ACTIVE_LIGHT_SENSORS[4] * I_vec[4] / PhysicalConst.LIGHT_SENSOR_NORMALS[4, 0]
                + ACTIVE_LIGHT_SENSORS[6] * I_vec[6] / PhysicalConst.LIGHT_SENSOR_NORMALS[6, 0]
            )

        if sun_body[1] == 0:  # YP / YM faces are dead
            sun_body[1] = (
                ACTIVE_LIGHT_SENSORS[5] * I_vec[5] / PhysicalConst.LIGHT_SENSOR_NORMALS[5, 1]
                + ACTIVE_LIGHT_SENSORS[7] * I_vec[7] / PhysicalConst.LIGHT_SENSOR_NORMALS[7, 1]
            )

    else:  # ZM face is either dead or not illuminated

        if sun_body[0] != 0:
            if sun_body[0] > 0:  # XP face is illuminated
                if ACTIVE_LIGHT_SENSORS[4]:  # Use ZP1 and remove X component to infer Z
                    sun_body[2] = (
                        I_vec[4] - sun_body[0] * PhysicalConst.LIGHT_SENSOR_NORMALS[4, 0]
                    ) / PhysicalConst.LIGHT_SENSOR_NORMALS[4, 2]
                else:  # Use the ZP3 sensor to directly get Z (this will not work if the rays are over 45 deg to Z)
                    sun_body[2] = ACTIVE_LIGHT_SENSORS[6] * I_vec[6] / PhysicalConst.LIGHT_SENSOR_NORMALS[6, 2]
            else:
                if ACTIVE_LIGHT_SENSORS[6]:  # Use ZP3 and subtract X influence to get Z
                    sun_body[2] = (
                        I_vec[6] - sun_body[0] * PhysicalConst.LIGHT_SENSOR_NORMALS[6, 0]
                    ) / PhysicalConst.LIGHT_SENSOR_NORMALS[6, 2]
                else:  # Use ZP1 to directly get Z (as long as rays are less than 45 deg to Z)
                    sun_body[2] = ACTIVE_LIGHT_SENSORS[6] * I_vec[4] / PhysicalConst.LIGHT_SENSOR_NORMALS[4, 2]

        else:  # At this point, we have no X axis readings
            return StatusConst.SUN_NOT_ENOUGH_READINGS, np.zeros((3,))

        if sun_body[1] != 0:
            if sun_body[1] > 0:  # YP face is illuminated
                if ACTIVE_LIGHT_SENSORS[5]:  # Use ZP2 and subtract effect of Y to get Z
                    sun_body[2] = (
                        I_vec[5] - sun_body[1] * PhysicalConst.LIGHT_SENSOR_NORMALS[5, 1]
                    ) / PhysicalConst.LIGHT_SENSOR_NORMALS[5, 2]
                else:  # use ZP4 to get Z (as long as rays are less than 45 deg to Z)
                    sun_body[2] = ACTIVE_LIGHT_SENSORS[7] * I_vec[7] / PhysicalConst.LIGHT_SENSOR_NORMALS[7, 2]

            else:
                if ACTIVE_LIGHT_SENSORS[7]:  # Use ZP4 and subtract effect of Y to get Z
                    z_est = (
                        I_vec[7] - sun_body[1] * PhysicalConst.LIGHT_SENSOR_NORMALS[7, 1]
                    ) / PhysicalConst.LIGHT_SENSOR_NORMALS[7, 2]
                else:  # Use ZP2 to directly get Z (as long as rays are less than 45 deg to Z)
                    z_est = ACTIVE_LIGHT_SENSORS[5] * I_vec[5] / PhysicalConst.LIGHT_SENSOR_NORMALS[5, 2]

                if sun_body[2] == 0:
                    sun_body[2] = z_est
                else:
                    sun_body[2] = (sun_body[2] + z_est) / 2  # Average estimates from X and Y axes
        else:  # At this point, we have no Y axis readings
            return StatusConst.SUN_NOT_ENOUGH_READINGS, np.zeros((3,))

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
