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


def REQUEST_TELEMETRY():
    """Requests telemetry data from the satellite."""
    logger.info("Executing REQUEST_TELEMETRY")
    pass
    # return True


def STREAM_TELEMETRY(time_duration, tm_type):
    """Streams telemetry data from the satellite."""
    logger.info("Executing STREAM_TELEMETRY")
    pass
    # return True


def STOP_STREAM_TELEMETRY():
    """Stops the telemetry data streaming."""
    logger.info("Executing STOP_STREAM_TELEMETRY")
    pass
    # return True


def SWITCH_TO_OVERRIDE_MODE(target_state):
    """Switches the satellite to override mode."""
    logger.info(f"Executing SWITCH_TO_OVERRIDE_MODE with target_state: {target_state}")
    pass
    # return True


def SWITCH_TO_AUTONOMOUS_MODE(initial_state):
    """Switches the satellite to autonomous mode."""
    logger.info(f"Executing SWITCH_TO_AUTONOMOUS_MODE with initial_state: {initial_state}")
    pass
    # return True


def TURN_OFF_DEVICE(device_id):
    """Turns off a specified device."""
    logger.info(f"Executing TURN_OFF_DEVICE with device_id: {device_id}")
    pass
    # return True


def TURN_ON_DEVICE(device_id):
    """Turns on a specified device."""
    logger.info(f"Executing TURN_ON_DEVICE with device_id: {device_id}")
    pass
    # return True


def REQUEST_FILE(file_tag, time_window):
    """Requests a file from the satellite."""
    logger.info(f"Executing REQUEST_FILE with file_tag: {file_tag} and time_window: {time_window}")
    pass
    # return True


def REQUEST_IMAGE(time_window):
    """Requests an image from the satellite."""
    logger.info(f"Executing REQUEST_IMAGE with time_window: {time_window}")
    pass
    # return True


def REQUEST_STORAGE_STATUS_MAINBOARD():
    """Requests the storage status of the mainboard."""
    logger.info("Executing REQUEST_STORAGE_STATUS_MAINBOARD")
    pass
    # return True


def REQUEST_STORAGE_STATUS_PAYLOAD():
    """Requests the storage status of the payload."""
    logger.info("Executing REQUEST_STORAGE_STATUS_PAYLOAD")
    pass
    # return True


def ENABLE_TASK(task_id, state_flags):
    """Enables a specified task."""
    logger.info(f"Executing ENABLE_TASK with task_id: {task_id} and state_flags: {state_flags}")
    pass
    # return True


def DISABLE_TASK(task_id, state_flags):
    """Disables a specified task."""
    logger.info(f"Executing DISABLE_TASK with task_id: {task_id} and state_flags: {state_flags}")
    pass
    # return True


def SCHEDULE_OD_EXPERIMENT(after_ground_pass):
    """Schedules an OD experiment."""
    logger.info(f"Executing SCHEDULE_OD_EXPERIMENT with after_ground_pass: {after_ground_pass}")
    pass
    # return True


def DOWNLINK_MISSION_DATA():
    """Downlinks mission data from the satellite."""
    logger.info("Executing DOWNLINK_MISSION_DATA")
    pass
    # return True
