from ulab import numpy as np


def rotation_matrix_from_vector(vec: np.ndarray) -> np.ndarray:
    """
    Compute the rotation matrix from a vector using Rodrigues' rotation formula.
    The input vector is assumed to be in the body-fixed reference frame.
    """
    # Compute the angle of rotation
    theta = np.linalg.norm(vec)
    if theta == 0:
        return np.eye(3)

    # Compute the unit rotation axis
    k = vec / theta

    # Compute the skew-symmetric matrix of k
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])

    # Compute the rotation matrix using Rodrigues' formula
    R = np.eye(3) + np.sin(theta) * K + (1 - np.cos(theta)) * np.dot(K, K)

    return R
