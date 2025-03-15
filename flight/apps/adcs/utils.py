from ulab import numpy as np


'''
    SENSOR VALIDITY CHECKS
'''

# GPS position validity checks
def is_valid_gps_state(r: np.ndarray, v:np.ndarray) -> bool:
    # Check Position
    if r is None or r.shape != (3,) or not(6.0e6 <= np.linalg.norm(r) <= 7.5e6):
            return False
    elif v is None or v.shape != (3,) or not(1.0e2 <= np.linalg.norm(v) <= 1.0e4):
            return False
    else:
            return True
    
# Magnetometer validity check
def is_valid_mag_reading(mag: np.ndarray) -> bool:
    if mag is None or len(mag) != 3:
        return False
    elif not (10 <= np.linalg.norm(mag) <= 100):  # Allowed between 10 and 100 uT (MSL : 58 uT, 600km : 37uT)
        return False
    else:
        return True
    
# Gyro validity check
def is_valid_gyro_reading(gyro: np.ndarray) -> bool:
    if gyro is None or len(gyro) != 3:
        return False
    elif not (0 <= np.linalg.norm(gyro) <= 1000):  # Setting a very (VERY) large upper bound
        return False
    else:
         return True