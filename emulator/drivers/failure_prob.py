from ulab import numpy as np


class torque_coil_prob:
    # Failure Probabilities:
    _prob_ = 2 * np.ones((5,))  # % of devices that throw [stall, ocp, ovt, tsd, npor] fault in a day

    scale = -86400 / (np.log(1 - (0.01 * _prob_)))  # exponential distribution scale


class sun_sensor_prob:
    # Failure Probabilities:
    _prob_ = 2 * np.ones((3,))  # % of devices that throw [flag_h, flag_l, overload] fault in a day

    scale = -86400 / (np.log(1 - (0.01 * _prob_)))  # exponential distribution scale


class rtc_prob:
    # Failure Probabilities:
    _prob_ = 2 * np.ones((2,))  # % of devices that throw [lost_power, battery_low] fault in a day

    scale = -86400 / (np.log(1 - (0.01 * _prob_)))  # exponential distribution scale


class imu_prob:
    # Failure Probabilities:
    _prob_ = np.array([2, 0.1])  # % of devices that throw [drop_cmd, fatal_err] fault in a day

    scale = -86400 / (np.log(1 - (0.01 * _prob_)))  # exponential distribution scale
