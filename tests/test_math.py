import numpy as np
import pytest

import tests.cp_mock  # noqa: F401
from flight.apps.adcs.math import rotation_matrix_from_vector


@pytest.fixture(
    params=[
        (np.array([0.0, 0.0, 0.0]), "identity"),
        (np.array([np.pi / 2, 0.0, 0.0]), "x_axis"),
        (np.array([0.0, np.pi / 2, 0.0]), "y_axis"),
        (np.array([0.0, 0.0, np.pi / 2]), "z_axis"),
        (np.array([0.5, 0.3, 0.2]), "orthogonal"),
        (np.array([0.01, 0.005, 0.008]), "small_angle"),
    ]
)
def test_vector(request):
    """Fixture providing test vectors."""
    return request.param[0], request.param[1]


def test_rotation_matrix_from_vector_shape(test_vector):
    """Test that result has correct shape."""
    vector, _ = test_vector
    result = rotation_matrix_from_vector(vector)
    assert result.shape == (3, 3)


def test_rotation_matrix_from_vector_identity(test_vector):
    """Test that zero vector returns identity matrix."""
    vector, case = test_vector
    if case != "identity":
        pytest.skip("Not identity case")
    result = rotation_matrix_from_vector(vector)
    expected = np.eye(3)
    np.testing.assert_array_almost_equal(result, expected)


def test_rotation_matrix_from_vector_orthogonal(test_vector):
    """Test that result is orthogonal matrix in SO(3)."""
    vector, _ = test_vector
    result = rotation_matrix_from_vector(vector)
    # R @ R^T = I (orthogonal property)
    np.testing.assert_array_almost_equal(result @ result.T, np.eye(3))
    # det(R) = 1 (special orthogonal group SO(3))
    assert np.isclose(np.linalg.det(result), 1.0)
