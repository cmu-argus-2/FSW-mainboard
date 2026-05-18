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

from apps.adcs.consts import StatusConst
from core import logger
from hal.configuration import SATELLITE
from micropython import const
from ulab import numpy as np

_MAX_RANGE = const(140000)  # OPT4001
_THRESHOLD_ILLUMINATION_LUX = const(3000)
_NUM_LIGHT_SENSORS = const(9)
_ERROR_LUX = const(-1)

# 1/sqrt(2) — normal component magnitude for 45-degree ZP sensors
_INV_SQRT2 = 0.70710678118

_FACES = ("XP", "XM", "YP", "YM", "ZP_XP", "ZP_YM", "ZP_XM", "ZP_YP", "ZM")


def read_light_sensors():
    """
    Read the light sensors on the x+,x-,y+,y-, and z- faces of the satellite.

    Returns:
        lux_readings: list of lux readings on each face. A "ERROR_LUX" reading comes from a dysfunctional sensor.
    """
    lux_readings = [_ERROR_LUX] * _NUM_LIGHT_SENSORS
    for i in range(_NUM_LIGHT_SENSORS):
        try:
            if SATELLITE.LIGHT_SENSOR_AVAILABLE(_FACES[i]):
                lux_readings[i] = SATELLITE.LIGHT_SENSORS[_FACES[i]].lux()
        except Exception as e:
            logger.warning(f"Error reading {_FACES[i]}: {e}")

    return lux_readings


def compute_body_sun_vector_from_lux(I_vec):
    """
    Get unit sun vector expressed in the body frame from solar flux values.

    Args:
        I_vec: flux values on each face in the following order
        - X+ face, X- face, Y+ face, Y- face, Z+/X+ face, Z+/Y- face, Z+/X- face, Z+/Y+ face, Z- face

    Returns:
        sun_body: unit vector from spacecraft to sun expressed in body frame
    """

    sun_body = np.zeros(3)

    num_valid_readings = _NUM_LIGHT_SENSORS - I_vec.count(_ERROR_LUX)
    if num_valid_readings == 0:
        return StatusConst.SUN_NO_READINGS, sun_body

    # Remap consts.py index order to structured solver order
    r0 = I_vec[0]  # XP
    r1 = I_vec[1]  # XM
    r2 = I_vec[2]  # YP
    r3 = I_vec[3]  # YM
    r4 = I_vec[8]  # ZM
    r5 = I_vec[4]  # ZP_XP
    r6 = I_vec[6]  # ZP_XM
    r7 = I_vec[7]  # ZP_YP
    r8 = I_vec[5]  # ZP_YM

    thr = _THRESHOLD_ILLUMINATION_LUX
    w0 = 1.0 if r0 > thr else 0.0
    w1 = 1.0 if r1 > thr else 0.0
    w2 = 1.0 if r2 > thr else 0.0
    w3 = 1.0 if r3 > thr else 0.0
    w4 = 1.0 if r4 > thr else 0.0
    w5 = 1.0 if r5 > thr else 0.0
    w6 = 1.0 if r6 > thr else 0.0
    w7 = 1.0 if r7 > thr else 0.0
    w8 = 1.0 if r8 > thr else 0.0

    # N^T W N: zero X-Y cross-term by geometry
    A = w0 + w1 + 0.5 * (w5 + w6)
    B = w2 + w3 + 0.5 * (w7 + w8)
    E = w4 + 0.5 * (w5 + w6 + w7 + w8)
    C = 0.5 * (w5 - w6)
    D = 0.5 * (w7 - w8)

    # A+B+E = sum of all weights/trace of N^T W N; zero means all valid sensors below threshold
    if A + B + E < 1e-8:
        return StatusConst.SUN_ECLIPSE, sun_body

    # Necessary and sufficient invertibility check
    if A < 1e-8 or B < 1e-8:
        return StatusConst.SUN_NOT_ENOUGH_READINGS, sun_body
    S = E - (C * C) / A - (D * D) / B
    if S < 1e-8:
        return StatusConst.SUN_NOT_ENOUGH_READINGS, sun_body

    # g = N^T W y
    gx = w0 * r0 - w1 * r1 + _INV_SQRT2 * (w5 * r5 - w6 * r6)
    gy = w2 * r2 - w3 * r3 + _INV_SQRT2 * (w7 * r7 - w8 * r8)
    gz = -w4 * r4 + _INV_SQRT2 * (w5 * r5 + w6 * r6 + w7 * r7 + w8 * r8)

    # (N^T W N) q = g solution
    qz = (gz - C * gx / A - D * gy / B) / S
    qx = (gx - C * qz) / A
    qy = (gy - D * qz) / B

    norm2 = qx * qx + qy * qy + qz * qz
    if norm2 < 1e-9:
        return StatusConst.ZERO_NORM, sun_body

    inv_norm = 1.0 / norm2 ** 0.5
    sun_body[0] = qx * inv_norm
    sun_body[1] = qy * inv_norm
    sun_body[2] = qz * inv_norm
    return StatusConst.OK, sun_body
