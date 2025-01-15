"""

Command Functions

======================

This modules contains the definition of the command functions for the satellite.


Each command is defined as follow:
- ID: A unique identifier for the command
- Name: A string representation of the command for debugging
- Description: A brief description of the command
- Arguments: A list of parameters that the command accepts
- Precondition: A list of conditions that must be met before executing the command

See documentation for a full description of each commands.

Author: Ibrahima S. Sow

"""

from core import logger


def SWITCH_TO_SAFE_MODE():
    """Force switches the satellite to SAFE mode."""
    logger.info("Executing SWITCH_TO_SAFE_MODE")
    pass


def SWITCH_TO_AUTONOMOUS_MODE(target_state):
    """Switches the satellite back to autonomous mode."""
    logger.info(f"Executing SWITCH_TO_AUTONOMOUS_MODE with target_state: {target_state}")
    pass


def ENABLE_DEVICE(device_id):
    """Enables the specified device and updates the configuration file."""
    logger.info(f"Executing ENABLE_DEVICE with device_id: {device_id}")
    pass


def DISABLE_DEVICE(device_id):
    """Disables the specified device and updates the configuration file."""
    logger.info(f"Executing DISABLE_DEVICE with device_id: {device_id}")
    pass


def ENABLE_TASK(task_id, state_flags):
    """Enables a task in a specific state or set of states."""
    logger.info(f"Executing ENABLE_TASK with task_id: {task_id} and state_flags: {state_flags}")
    pass


def DISABLE_TASK(task_id, state_flags):
    """Disables a task in a specific state or set of states."""
    logger.info(f"Executing DISABLE_TASK with task_id: {task_id} and state_flags: {state_flags}")
    pass


def REQUEST_TELEMETRY(tm_type):
    """Requests telemetry data from the satellite."""
    logger.info(f"Executing REQUEST_TELEMETRY with tm_type: {tm_type}")
    pass


def REQUEST_FILE(file_tag, time_window=None):
    """Requests a specific file from the satellite."""
    logger.info(f"Executing REQUEST_FILE with file_tag: {file_tag} and time_window: {time_window}")
    pass


def REQUEST_IMAGE():
    """Requests an image from the satellite storage."""
    logger.info("Executing REQUEST_IMAGE")
    pass


def REQUEST_STORAGE_STATUS():
    """Requests the storage status of the mainboard."""
    logger.info("Executing REQUEST_STORAGE_STATUS")
    pass


def SCHEDULE_OD_EXPERIMENT():
    """Schedules an orbit determination experiment."""
    logger.info("Executing SCHEDULE_OD_EXPERIMENT")
    pass


def DOWNLINK_MISSION_DATA():
    """Downlinks mission data to the ground station."""
    logger.info("Executing DOWNLINK_MISSION_DATA")
    pass
