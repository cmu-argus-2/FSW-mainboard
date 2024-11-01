"""
Command Processor Engine

======================

This modules contains the command processing logic for the satellite. Once the communication subsystem decodes a ground station
command, the command processor interprets the command and executes the corresponding action.
The command processor is responsible for validating the command, executing the command, and
eventually providing a response about the command execution status.

Each command is defined as follow:
- ID: A unique identifier for the command
- Name: A string representation of the command for debugging
- Description: A brief description of the command
- Arguments: A list of parameters that the command accepts
- Precondition: A list of conditions that must be met before executing the command

See documentation for a full description of each commands.

Author: Ibrahima S. Sow
"""

from core import DataHandler as DH
from core import logger
from core.states import STATES
from hal.configuration import SATELLITE

# A command is defined as a tuple with the following elements:
# (ID, precondition, argument list, execute function)
COMMANDS = [
    # REQUEST_TELEMETRY (no precondition needed)
    (0x01, lambda: True, [], lambda args: REQUEST_TELEMETRY()),
    # STREAM_TELEMETRY (requires NOMINAL or DOWNLINK state)
    (0x02, lambda: SATELLITE.state in [STATES.NOMINAL, STATES.DOWNLINK], [], lambda args: STREAM_TELEMETRY()),
    # STOP_STREAM_TELEMETRY (requires TM streaming mode)
    (
        0x03,
        lambda: True,  # TODO: Add a condition to check if telemetry is being streamed
        [],
        lambda args: STOP_STREAM_TELEMETRY(),
    ),
    # SWITCH_TO_OVERRIDE_MODE (requires autonomous mode)
    (
        0x04,
        lambda: True,  # TODO: Add a condition to check if the state is in autonomous mode
        ["target_state"],
        lambda args: SWITCH_TO_OVERRIDE_MODE(args[0]),
    ),
    # SWITCH_TO_AUTONOMOUS_MODE (requires override mode)
    (
        0x05,
        lambda: True,  # TODO: Add a condition to check if the state is in override mode
        ["initial_state"],
        lambda args: SWITCH_TO_AUTONOMOUS_MODE(args[0]),
    ),
    # TURN_OFF_DEVICE (requires device to be ON)
    (
        0x06,
        lambda device_id: True,  # TODO Add a condition to check if the device is ON
        ["device_id"],
        lambda args: TURN_OFF_DEVICE(args[0]),
    ),
    # TURN_ON_DEVICE (requires device to be OFF)
    (
        0x07,
        lambda device_id: True,  # TODO Add a condition to check if the device is OFF
        ["device_id"],
        lambda args: TURN_ON_DEVICE(args[0]),
    ),
    # REQUEST_FILE (requires file process to exist)
    (
        0x08,
        lambda tag: True,  # TODO Add a condition to check if the file process exists
        ["file_tag", "time_window"],
        lambda args: REQUEST_FILE(args[0], args[1]),
    ),
    # REQUEST_IMAGE (requires presence of images)
    (
        0x09,
        lambda: True,  # TODO Add a condition to check if images are available
        ["time_window"],
        lambda args: REQUEST_IMAGE(args[0]),
    ),
    # REQUEST_STORAGE_STATUS_MAINBOARD (no precondition needed)
    (0x0A, lambda: True, [], lambda args: REQUEST_STORAGE_STATUS_MAINBOARD()),
    # REQUEST_STORAGE_STATUS_PAYLOAD (turn on payload if needed)
    (
        0x0B,
        lambda: True,  # TODO Add a condition to check if the payload is ON OR
        ["turn_on_payload"],
        lambda args: REQUEST_STORAGE_STATUS_PAYLOAD(),
    ),
    # ENABLE_TASK (requires Task ID to exist)
    (
        0x0C,
        lambda task_id: True,  # TODO Add a condition to check if the task exists
        ["task_id", "state_flags"],
        lambda args: ENABLE_TASK(args[0], args[1]),
    ),
    # DISABLE_TASK (requires Task ID to exist)
    (
        0x0D,
        lambda task_id: True,  # TODO Add a condition to check if the task exists
        ["task_id", "state_flags"],
        lambda args: DISABLE_TASK(args[0], args[1]),
    ),
    # SCHEDULE_OD_EXPERIMENT (requires power available)
    (
        0x0E,
        lambda: True,  # TODO Add a condition to check if enough power is available from EPS or add it to the task list
        ["after_ground_pass"],
        lambda args: SCHEDULE_OD_EXPERIMENT(args[0]),
    ),
    # DOWNLINK_MISSION_DATA (no precondition needed)
    (0x0F, lambda: True, [], lambda args: DOWNLINK_MISSION_DATA()),
]


def process_command(cmd_id, *args):
    """Processes a command by ID and arguments, with lightweight validation and execution."""
    for command in COMMANDS:
        if command[0] == cmd_id:
            precondition, arg_list, execute = command[1], command[2], command[3]

            # Verify precondition
            if not precondition():
                logger.log("Precondition failed")
                return False

            # Verify the argument count
            if len(args) != len(arg_list):
                logger.log(f"Argument count mismatch for command ID {cmd_id}")
                return False

            # Execute the command function with arguments
            return execute(args)

    logger.warning("Unknown command ID")
    return False


# Command function definitions
def REQUEST_TELEMETRY():
    """Requests telemetry data from the satellite."""
    logger.info("Executing REQUEST_TELEMETRY")
    pass
    # return True


def STREAM_TELEMETRY():
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
