"""

Command Definitions

======================

This modules contains the definition of the command functions for the satellite.


Each command is defined as follows:
- ID: A unique identifier for the command.
- Name: A string representation of the command for debugging.
- Description: A brief description of the command.
- Arguments: A list of parameters that the command accepts.
- Precondition: A list of conditions that must be met before executing the command.

See the documentation for a full description of each command.

Author: Ibrahima S. Sow

"""

from core import logger
from core import state_manager as SM
from core.states import STATES, STR_STATES


def FORCE_REBOOT():
    """Forces a power cycle of the spacecraft."""
    logger.info("Executing FORCE_REBOOT")
    # https://learn.adafruit.com/circuitpython-essentials/circuitpython-resetting
    pass


def SWITCH_TO_STATE(target_state_id, time_in_state=None):
    """Forces a switch of the spacecraft to a specific state."""
    SM.switch_to(target_state_id)
    logger.info(f"Executing SWITCH_TO_STATE with target_state: {STR_STATES[target_state_id]}")
    pass


def UPLINK_TIME_REFERENCE(time_in_state):
    """Sends a time reference to the spacecraft to update the time processing module."""
    logger.info(f"Executing UPLINK_TIME_REFERENCE with current_time: {current_time}")
    pass


def UPLINK_ORBIT_REFERENCE(time_in_state, orbital_parameters):
    """Sends time-referenced orbital information to update the orbit reference."""
    logger.info(f"Executing UPLINK_ORBIT_REFERENCE with orbital_parameters: {orbital_parameters}")
    pass


def TURN_OFF_PAYLOAD():
    """Sends a shutdown command to the payload and turns off its power line."""
    logger.info("Executing TURN_OFF_PAYLOAD")
    pass


def SCHEDULE_OD_EXPERIMENT():
    """Schedules an orbit determination experiment at the next available opportunity."""
    logger.info("Executing SCHEDULE_OD_EXPERIMENT")
    pass


def REQUEST_TM_HEARTBEAT():
    """Requests a nominal snapshot of all subsystems."""
    logger.info("Executing REQUEST_TM_HEARTBEAT")
    pass


def REQUEST_TM_HAL():
    """Requests hardware-focused telemetry, including information on HAL, EPS, and errors."""
    logger.info("Executing REQUEST_TM_HAL")
    pass


def REQUEST_TM_STORAGE():
    """Requests full storage status of the mainboard, including details on onboard processes."""
    logger.info("Executing REQUEST_TM_STORAGE")
    pass


def REQUEST_TM_PAYLOAD():
    """Requests telemetry data from the payload, provided it is on."""
    logger.info("Executing REQUEST_TM_PAYLOAD")
    pass


def REQUEST_FILE_METADATA(file_tag, requested_time=None):
    """Requests metadata for a specific file from the spacecraft."""
    logger.info(f"Executing REQUEST_FILE_METADATA with file_tag: {file_tag} and requested_time: {requested_time}")
    pass


def REQUEST_FILE_PKT(file_tag):
    """Requests a specific file packet from the spacecraft."""
    logger.info(f"Executing REQUEST_FILE_PKT with file_tag: {file_tag}")
    pass


def REQUEST_IMAGE():
    """Requests an image from the spacecraft's internal storage."""
    logger.info("Executing REQUEST_IMAGE")
    pass
