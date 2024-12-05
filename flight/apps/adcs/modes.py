"""
Operational modes for the attitude determination and control system (ADCS) of the satellite.

DETUMBLING:
- This mode detumbles the satellite to a target angular rate. It is triggered right
after the satellite is deployed from the launch vehicle or when the angular rate reaches
a triggering threshold.

SPIN_STABILIZATION:
- This mode stabilizes the satellite's spin axis to a fixed direction. It is triggered after
the DETUMBLING reaches its predefined target rate or when the Sun Vector is lost (e.g. eclipse)
in SUN_POINTING mode.

SUN_POINTING:
- This mode points the spin axis of the satellite towards the sun. It is triggered when the
satellite is spin stabilized and the Sun Vector is detected. Given the inertially fixed direction
of the Sun, the satellite can maintain the desired attitude passively. If the Sun Vector is lost,
the satellite will default to SPIN_STABILIZATION mode.
"""


class ADCSMode:
    DETUMBLING = 0  # Detumbling to a target rate --> spinning the satellite to a fixed rate
    SPIN_STABILIZATION = 1  # Spin stabilizing  --> fixing the angular momentum
    SUN_POINTING = 2  # Sun Pointing: matchign the angular momentum with the sun vector


# CONSTANTS
DETUMBLING_TARGET_ANGULAR_RATE = 0.05  # rad/s --> 2.86 deg/s
SPIN_STABILIZATION_TOLERANCE = 0.5  # deg --> 0.0087 rad/s
SUN_POINTING_TOLERANCE = 0.09  # ~ 5 deg
