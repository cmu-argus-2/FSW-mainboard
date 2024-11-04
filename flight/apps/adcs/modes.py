"""
Operational states for the attitude determination and control system (ADCS) of the satellite.

TODO

"""


class OperationalADCS:
    DetumblingMode = 0  # Detumbling mode, no pointing, within acceptable treshold
    MissionMode = 1  # Sun-pointing, small spinning rate and acceptable wobble
    SafePowerPositiveMode = 2  # Sun-pointing, safe Power Positive Mode and high spinning rate
