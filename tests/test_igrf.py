from datetime import datetime as dt
from datetime import timezone

import numpy as np
import pytest

import tests.cp_mock  # noqa: F401
from flight.apps.adcs.igrf import igrf, igrf_eci

EARTH_RADIUS = 6.378136300e3  # km


def timestamp(year, month, day, hour=0, minute=0, second=0):
    return dt(year, month, day, hour, minute, second, tzinfo=timezone.utc).timestamp()


def assert_vector_similar(a, b, leq, angle_tolerance=5, a_tolerance=50, units=""):
    ua = a / np.linalg.norm(a)
    ub = b / np.linalg.norm(b)
    angle = np.arccos(np.dot(ua, ub)) * 180 / np.pi
    dif = np.linalg.norm(a - b)
    leq(angle, angle_tolerance, f"Exceeded the {angle_tolerance}° tolerance\n ref: {b}\n ours:   {a}\n diff:   {b - a}")
    leq(dif, a_tolerance, f"Exceeded the {a_tolerance}{units} tolerance\n ref: {b}\n ours:   {a}\n diff:   {b - a}")
    return angle, dif


def similar(a, b, a_tolerance=3000, angle_tolerance=5.0, units="nT"):
    assert_vector_similar(a, b, pytest.approx, a_tolerance=a_tolerance, angle_tolerance=angle_tolerance, units=units)


def test_matches_IGRF13():
    # Test data generated from https://www.ngdc.noaa.gov/IAGA/vmod/igrf.html using pyIGRF.py
    # Note that we use geocentric coordinates and compare with the IGRF13 results
    t = timestamp(2020, 4, 19, 15)  # time is about 2020.3
    similar(igrf(t, 34.567, 45.678, 6697.043115), [24354.4, 1908.4, 32051.6])

    t = timestamp(2023, 1, 1)
    similar(igrf(t, -12, 37, 6700), [20274.2, -1994.6, -18852.8])

    t = timestamp(2022, 7, 2, 22)
    similar(
        igrf(t, 25, 35, EARTH_RADIUS + 400),  # about the ISS altitude
        [28295.864360612726, 1850.2071187341612, 21436.550334577572],
    )

    t = timestamp(2023, 1, 1)
    similar(igrf(t, -79, 48, EARTH_RADIUS + 700), [4650.9, -10831.9, -34896.3])


def test_no_changes():
    """Test that our changes to the IGRF model do not change the results."""
    t = timestamp(2020, 4, 19, 15)
    np.testing.assert_array_almost_equal(
        igrf(t, 34.567, 45.678, 6697.043115), [24694.17511877, 2125.5475454, 32160.37154219], decimal=1
    )

    t = timestamp(2021, 7, 28, 2)
    np.testing.assert_array_almost_equal(igrf(t, -12, 127, 6873), [28092.523258, 1432.59565072, -22804.66673182], decimal=1)


def similar_eci(a, b, a_tolerance=30, angle_tolerance=1.0, units="nT"):
    assert_vector_similar(a, b, pytest.approx, a_tolerance=a_tolerance, angle_tolerance=angle_tolerance, units=units)


def test_close_GN():
    """Test that our IGRF in ECI coordinates is close to the results from GravNav."""
    t = timestamp(2020, 9, 15)
    similar_eci(igrf_eci(t, [7000, 7500, 9300]), [-2958.36063183389, -3285.782343814322, -751.7865862535493])

    t = timestamp(2021, 4, 1)
    similar_eci(igrf_eci(t, [7654, -12345, 5678]), [-963.4031953585253, 1522.7638883411967, 1657.0123037449737])

    t = timestamp(2020, 8, 13)
    similar_eci(igrf_eci(t, [8763, -7421, -9213]), [1978.9330574152757, -2226.2182265227348, -306.67003898572216])
