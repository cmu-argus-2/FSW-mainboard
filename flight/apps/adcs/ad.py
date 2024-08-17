"""

Attitude Determination Module for the Attitude Determination and Control Subsystem (ADCS).

This module is responsible for processing GNC sensor data to determine the satellite's attitude.

Argus possesses a 3-axis IMU (Inertial Measurement Unit) providing angular rate, acceleration, and
magnetic field data on the mainboard. A Star Tracker is also present on the Z- face if the spacecraft,
providing attitude quaternion at X Hz for fine attitude determination.

"""

from ulab import numpy as np


def rotm2quat(r):
    """
    Convert a rotation matrix to a quaternion.

    Args:
        r (np.ndarray): Rotation matrix.

    Returns:
        np.ndarray: Quaternion [q0, q1, q2, q3].
    """
    q = np.zeros(4)
    q[0] = 0.5 * np.sqrt(1 + r[0, 0] + r[1, 1] + r[2, 2])
    q[1] = (1 / (4 * q[0])) * (r[2][1] - r[1][2])
    q[2] = (1 / (4 * q[0])) * (r[0][2] - r[2][0])
    q[3] = (1 / (4 * q[0])) * (r[1][0] - r[0][1])
    return np.array(q)


def TRIAD(n1, n2, b1, b2):

    n1 = np.array(n1)
    n2 = np.array(n2)
    b1 = np.array(b1)
    b2 = np.array(b2)

    # Normalize the input vectors
    n1 /= np.linalg.norm(n1)
    n2 /= np.linalg.norm(n2)
    b1 /= np.linalg.norm(b1)
    b2 /= np.linalg.norm(b2)

    # Inertial triad
    t1 = n1
    t2 = np.cross(n1, n2) / np.linalg.norm(np.cross(n1, n2))  # Third linearly independant vector
    t3 = np.cross(t1, t2) / np.linalg.norm(np.cross(t1, t2))
    T = np.array([t1, t2, t3]).transpose()

    # Body triad
    w1 = b1
    w2 = np.cross(b1, b2) / np.linalg.norm(np.cross(b1, b2))
    w3 = np.cross(w1, w2) / np.linalg.norm(np.cross(w1, w2))
    W = np.array([w1, w2, w3]).transpose()

    # Determine attitude
    Q = np.dot(T, W.transpose())

    return rotm2quat(Q)
