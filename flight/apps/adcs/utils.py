from ulab import numpy as np

"""
    SENSOR VALIDITY CHECKS
"""

_MIN_POSITION_NORM = 6.0e6  # Min allowed position is 6000 km from Earth centre (~300km underground)
_MAX_POSITION_NORM = 7.5e6  # Max allowed position is 7500 km (~1200km altitude)
_MIN_VELOCITY_NORM = 0.0  # Min alllowed ECEF velocity is 0 m/s (Earth surface velocity is 0 m/s)
_MAX_VELOCITY_NORM = 1.0e4  # Max allowed velocity is 10 km/s (Expected rbital velocity is 7-8km/s)

_MIN_MAG_NORM = 1.0e-5  # Min allowed magnetometer reading is 10 uT (Expected field strength in orbit is ~40 uT)
_MAX_MAG_NORM = 1.0e-4  # Max allowed magnetometer reading is 100 uT (Field strength at Mean Sea Level is ~60 uT)

_MAX_GYRO_NORM = 1.0e3  # Max allowed gyro angular velocity is 1000 rad/s (Expect to detumble at ~30 deg/s)


def is_valid_gps_state(r: np.ndarray, v: np.ndarray) -> bool:
    # GPS position validity checks on ECEF state
    # Check Position
    if r is None or r.shape != (3,) or not (_MIN_POSITION_NORM <= np.linalg.norm(r) <= _MAX_POSITION_NORM):
        return False
    elif v is None or v.shape != (3,) or not (_MIN_VELOCITY_NORM <= np.linalg.norm(v) <= _MAX_VELOCITY_NORM):
        return False
    else:
        return True


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
