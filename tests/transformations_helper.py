import numpy as np
from scipy.linalg import expm


def skew_symmetric(w):
    """
    Compute the skew symmetric form of a vector.

    Args:
        w (np.ndarray): Vector [w1, w2, w3].

    Returns:
        np.ndarray: Skew symmetric matrix.
    """
    return np.array([[0, -w[2], w[1]], [w[2], 0, -w[0]], [-w[1], w[0], 0]])


def L(q):
    """
    Left-multiply a quaternion.

    Args:
        q (np.ndarray): Quaternion [q0, q1, q2, q3].

    Returns:
        np.ndarray: Left-multiplied quaternion.
    """
    L = np.zeros((4, 4))
    L[0, 0] = q[0]
    L[0, 1:] = -q[1:]
    L[1:, 0] = q[1:]
    L[1:, 1:] = q[0] * np.identity(3) + skew_symmetric(q[1:])
    return L


def R(q):
    """
    Right-multiply a quaternion.

    Args:
        q (np.ndarray): Quaternion [q0, q1, q2, q3].

    Returns:
        np.ndarray: Right-multiplied quaternion.
    """
    R = np.zeros((4, 4))
    R[0, 0] = q[0]
    R[0, 1:] = -q[1:]
    R[1:, 0] = q[1:]
    R[1:, 1:] = q[0] * np.identity(3) - skew_symmetric(q[1:])
    return R


def conj(q):
    """
    Compute the conjugate of a quaternion.

    Args:
        q (np.ndarray): Quaternion [q0, q1, q2, q3].

    Returns:
        np.ndarray: Conjugate of the quaternion.
    """
    qr = np.zeros(4)
    qr[0] = q[0]
    qr[1:] = -q[1:]
    return qr


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


def dcm_from_q(q):
    """
    Convert a quaternion to a direction cosine matrix (DCM).

    Args:
        q (np.ndarray): Quaternion [q0, q1, q2, q3].

    Returns:
        np.ndarray: Direction cosine matrix (DCM).
    """
    norm = np.linalg.norm(q)
    q0, q1, q2, q3 = q / norm if norm != 0 else q

    # DCM
    Q = np.array(
        [
            [
                2 * q1**2 + 2 * q0**2 - 1,
                2 * (q1 * q2 - q3 * q0),
                2 * (q1 * q3 + q2 * q0),
            ],
            [
                2 * (q1 * q2 + q3 * q0),
                2 * q2**2 + 2 * q0**2 - 1,
                2 * (q2 * q3 - q1 * q0),
            ],
            [
                2 * (q1 * q3 - q2 * q0),
                2 * (q2 * q3 + q1 * q0),
                2 * q3**2 + 2 * q0**2 - 1,
            ],
        ]
    )

    return Q


def quat_to_axisangle(q):
    """
    Convert a quaternion to axis-angle representation.

    Args:
        q (np.ndarray): Quaternion [q0, q1, q2, q3].

    Returns:
        np.ndarray: Axis-angle representation [axis_x, axis_y, axis_z, angle].
    """
    axis = np.zeros(3)
    angle = 2 * np.arccos(q[0])
    axis = q[1:] / np.sqrt(1 - q[0] * q[0])
    return np.concatenate((axis, [angle]))


def dcm_from_phi(Φ):
    """
    Compute the direction cosine matrix (DCM) from an axis-angle representation.

    Args:
        Φ (np.ndarray): Axis-angle representation [axis_x, axis_y, axis_z, angle].

    Returns:
        np.ndarray: Direction cosine matrix (DCM).
    """
    return expm(skew_symmetric(Φ))
