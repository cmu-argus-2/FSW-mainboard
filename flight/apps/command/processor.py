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

from apps.command.commands import (
    DISABLE_TASK,
    DOWNLINK_MISSION_DATA,
    ENABLE_TASK,
    REQUEST_FILE,
    REQUEST_IMAGE,
    REQUEST_STORAGE_STATUS_MAINBOARD,
    REQUEST_STORAGE_STATUS_PAYLOAD,
    REQUEST_TELEMETRY,
    SCHEDULE_OD_EXPERIMENT,
    STOP_STREAM_TELEMETRY,
    STREAM_TELEMETRY,
    SWITCH_TO_AUTONOMOUS_MODE,
    SWITCH_TO_OVERRIDE_MODE,
    TURN_OFF_DEVICE,
    TURN_ON_DEVICE,
)
from core import DataHandler as DH
from core import logger
from core.states import STATES
from hal.configuration import SATELLITE

# A command is defined as a tuple with the following elements:
# - ID: A unique identifier for the command
# - Precondition: A function that checks if the command can be executed
# - Arguments: A list of parameters that the command accepts
# - Execute: The function that executes the command

# See commands.py for function definitions (command functions and eventual preconditions)

COMMANDS = [
    # REQUEST_TELEMETRY (no precondition needed)
    (
        0x01,
        lambda: True,
        [],
        REQUEST_TELEMETRY,
    ),
    # STREAM_TELEMETRY (requires NOMINAL, DOWNLINK, SAFE state)
    (
        0x02,
        lambda: True,  # TODO: Add a state precondition
        ["time_duration", "tm_type"],
        STREAM_TELEMETRY,
    ),
    # STOP_STREAM_TELEMETRY (requires TM streaming mode)
    (
        0x03,
        lambda: True,  # TODO: Add a condition to check if telemetry is being streamed
        [],
        STOP_STREAM_TELEMETRY,
    ),
    # SWITCH_TO_OVERRIDE_MODE (requires autonomous mode)
    (
        0x04,
        lambda: True,  # TODO: Add a condition to check if the state is in autonomous mode
        ["target_state"],
        SWITCH_TO_OVERRIDE_MODE,
    ),
    # SWITCH_TO_AUTONOMOUS_MODE (requires override mode)
    (
        0x05,
        lambda: True,  # TODO: Add a condition to check if the state is in override mode
        ["initial_state"],
        SWITCH_TO_AUTONOMOUS_MODE,
    ),
    # TURN_OFF_DEVICE (requires device to be ON)
    (
        0x06,
        lambda device_id: True,  # TODO Add a condition to check if the device is ON
        ["device_id"],
        TURN_OFF_DEVICE,
    ),
    # TURN_ON_DEVICE (requires device to be OFF)
    (
        0x07,
        lambda device_id: True,  # TODO Add a condition to check if the device is OFF
        ["device_id"],
        TURN_ON_DEVICE,
    ),
    # REQUEST_FILE (requires file process to exist)
    (
        0x08,
        lambda tag: True,  # TODO Add a condition to check if the file process exists
        ["file_tag", "time_window"],
        REQUEST_FILE,
    ),
    # REQUEST_IMAGE (requires presence of images)
    (
        0x09,
        lambda: True,  # TODO Add a condition to check if images are available
        ["time_window"],
        REQUEST_IMAGE,
    ),
    # REQUEST_STORAGE_STATUS_MAINBOARD (no precondition needed)
    (
        0x0A,
        lambda: True,
        [],
        REQUEST_STORAGE_STATUS_MAINBOARD,
    ),
    # REQUEST_STORAGE_STATUS_PAYLOAD (turn on payload if needed)
    (
        0x0B,
        lambda: True,  # TODO Add a condition to check if the payload is ON OR
        ["turn_on_payload"],
        REQUEST_STORAGE_STATUS_PAYLOAD,
    ),
    # ENABLE_TASK (requires Task ID to exist)
    (
        0x0C,
        lambda task_id: True,  # TODO Add a condition to check if the task exists
        ["task_id", "state_flags"],
        ENABLE_TASK,
    ),
    # DISABLE_TASK (requires Task ID to exist)
    (
        0x0D,
        lambda task_id: True,  # TODO Add a condition to check if the task exists
        ["task_id", "state_flags"],
        DISABLE_TASK,
    ),
    # SCHEDULE_OD_EXPERIMENT (requires power available)
    (
        0x0E,
        lambda: True,  # TODO Add a condition to check if enough power is available from EPS or add it to the task list
        ["after_ground_pass"],
        SCHEDULE_OD_EXPERIMENT,
    ),
    # DOWNLINK_MISSION_DATA (no precondition needed)
    (
        0x0F,
        lambda: True,
        [],
        DOWNLINK_MISSION_DATA,
    ),
]


class CommandProcessingStatus:
    COMMAND_EXECUTION_SUCCESS = 0x00
    UNKNOWN_COMMAND_ID = 0x01
    PRECONDITION_FAILED = 0x02
    ARGUMENT_COUNT_MISMATCH = 0x03
    COMMAND_EXECUTION_FAILED = 0x04  # Maybe write error stack to a file/log ?


def process_command(cmd_id, *args):
    """Processes a command by ID and arguments, with lightweight validation and execution."""
    for command in COMMANDS:
        if command[0] == cmd_id:
            precondition, arg_list, execute = command[1:]

            # Verify precondition
            if not precondition():
                logger.error("Cmd: Precondition failed")
                return CommandProcessingStatus.PRECONDITION_FAILED

            # Verify the argument count
            if len(args) != len(arg_list):
                logger.error(f"Cmd: Argument count mismatch for command ID {cmd_id}")
                return CommandProcessingStatus.ARGUMENT_COUNT_MISMATCH

            # Execute the command function with arguments
            try:
                execute(*args)
                return CommandProcessingStatus.COMMAND_EXECUTION_SUCCESS
            except Exception as e:
                logger.error(f"Cmd: Command execution failed: {e}")
                # Optionally log stack trace to a file for deeper diagnostics
                return CommandProcessingStatus.COMMAND_EXECUTION_FAILED

    logger.warning("Cmd: Unknown command ID")
    return CommandProcessingStatus.UNKNOWN_COMMAND_ID


def handle_command_execution_status(status):
    # TODO: Implement response handling based on the command execution status
    # If the command execution was successful, send a success response
    # If the command execution failed, send an error response with the error code

    if status == CommandProcessingStatus.COMMAND_EXECUTION_SUCCESS:
        logger.info("Command execution successful")
        # TODO build success response
    else:  # All other cases are errors
        # TODO build error response
        pass
