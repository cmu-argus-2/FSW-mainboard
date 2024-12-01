from ulab import numpy as np


def skew(v: np.ndarray):
    return np.array(
        [
            [0.0, -v[2], v[1]],
            [v[2], 0.0, -v[0]],
            [-v[1], v[0], 0.0],
        ]
    )


def is_near(a: float, b: float, tol=1e-6) -> bool:
    return abs(a - b) < tol
