"""
This module will provide online orbit tracking/propagation capabilities based on a simple dynamics model.
It leverages orbit information, either from the GPS module or uplinked information from the groud.

"""

from ulab import numpy as np

def propagate_orbit(current_time : int, last_update_time : int, last_updated_position : np.ndarray) -> np.ndarray:
    pass
