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
    DISABLE_DEVICE,
    DISABLE_TASK,
    DOWNLINK_MISSION_DATA,
    ENABLE_DEVICE,
    ENABLE_TASK,
    REQUEST_FILE,
    REQUEST_IMAGE,
    REQUEST_STORAGE_STATUS,
    REQUEST_TELEMETRY,
    SCHEDULE_OD_EXPERIMENT,
    SWITCH_TO_AUTONOMOUS_MODE,
    SWITCH_TO_SAFE_MODE,
)
from core import logger

# See commands.py for function definitions (command functions and eventual preconditions)
# A command is defined as a tuple with the following elements:
# - ID: A unique identifier for the command
# - Precondition: A function that checks if the command can be executed
# - Arguments: A list of parameters that the command accepts
# - Execute: The function that executes the command

COMMANDS = [
    (
        0x01,
        lambda: True,
        [],
        SWITCH_TO_SAFE_MODE,
    ),
    (
        0x02,
        lambda: True,  # TODO: Validate the target state
        ["target_state"],
        SWITCH_TO_AUTONOMOUS_MODE,
    ),
    (
        0x03,
        lambda device_id: True,  # TODO: Check if the device is ON
        ["device_id"],
        ENABLE_DEVICE,
    ),
    (
        0x04,
        lambda device_id: True,  # TODO: Check if the device is OFF
        ["device_id"],
        DISABLE_DEVICE,
    ),
    (
        0x05,
        lambda task_id: True,  # TODO: Ensure the task ID exists
        ["task_id", "state_flags"],
        ENABLE_TASK,
    ),
    (
        0x06,
        lambda task_id: True,  # TODO: Ensure the task ID exists
        ["task_id", "state_flags"],
        DISABLE_TASK,
    ),
    (
        0x07,
        lambda: True,
        ["tm_type"],
        REQUEST_TELEMETRY,
    ),
    (
        0x08,
        lambda file_tag: True,  # TODO: Validate if the file exists
        ["file_tag", "time_window"],
        REQUEST_FILE,
    ),
    (
        0x09,
        lambda: True,  # TODO: Check for image availability
        [],
        REQUEST_IMAGE,
    ),
    (
        0x0A,
        lambda: True,
        [],
        REQUEST_STORAGE_STATUS,
    ),
    (
        0x0B,
        lambda: True,  # TODO: Check for power and readiness
        [],
        SCHEDULE_OD_EXPERIMENT,
    ),
    (
        0x0C,
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
                print(arg_list)
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
