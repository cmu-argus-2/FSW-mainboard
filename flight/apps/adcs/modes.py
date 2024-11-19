"""
Operational modes for the attitude determination and control system (ADCS) of the satellite.

TUMBLING:
- This mode detumbles the satellite to a target angular rate. It is triggered right
after the satellite is deployed from the launch vehicle or when the angular rate reaches
a triggering threshold.

STABLE:
- This mode stabilizes the satellite's spin axis to a fixed direction. It is triggered after
the TUMBLING reaches its predefined target rate or when the Sun Vector is lost (e.g. eclipse)
in SUN_POINTED mode.

SUN_POINTED:
- This mode points the spin axis of the satellite towards the sun. It is triggered when the
satellite is spin stabilized and the Sun Vector is detected. Given the inertially fixed direction
of the Sun, the satellite can maintain the desired attitude passively. If the Sun Vector is lost,
the satellite will default to STABLE mode.
"""

from ulab import numpy as np

TUMBLING = 0  # Satellite is spinning outside the "stable" bounds.
STABLE = 1  # Satellite is spinning inside the "stable" bounds.
SUN_POINTED = 2  # Satellite is generally pointed towards the sun.


class Constants:
    STABLE_TOLERANCE = 0.05  # Considered "stable" if ang vel < 0.05 rad/s = 2.86 deg/s.
    SUN_POINTED_TOLERANCE = 0.09  # Considered "sun-pointed" if att err < 0.09 rad = 5 deg.
    SUN_VECTOR_REFERENCE = np.array([0.0, 0.0, 1.0])
