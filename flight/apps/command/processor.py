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
    FORCE_REBOOT,
    REQUEST_FILE_METADATA,
    REQUEST_FILE_PKT,
    REQUEST_IMAGE,
    REQUEST_TM_HAL,
    REQUEST_TM_HEARTBEAT,
    REQUEST_TM_PAYLOAD,
    REQUEST_TM_STORAGE,
    SCHEDULE_OD_EXPERIMENT,
    SWITCH_TO_STATE,
    TURN_OFF_PAYLOAD,
    UPLINK_ORBIT_REFERENCE,
    UPLINK_TIME_REFERENCE,
)
from core import logger

# See commands.py for function definitions (command functions and eventual preconditions)
# A command is defined as a tuple with the following elements:
# - ID: A unique identifier for the command
# - Precondition: A function that checks if the command can be executed
# - Arguments: A list of parameters that the command accepts
# - Execute: The function that executes the command

COMMANDS = [
    (0x00, lambda: True, [], FORCE_REBOOT),
    (0x01, lambda: True, ["target_state_id", "time_in_state"], SWITCH_TO_STATE),
    (0x02, lambda: True, ["time_in_state"], UPLINK_TIME_REFERENCE),
    (0x03, lambda: True, ["time_in_state", "orbital_parameters"], UPLINK_ORBIT_REFERENCE),
    (0x04, lambda: True, [], TURN_OFF_PAYLOAD),
    (0x05, lambda: True, [], SCHEDULE_OD_EXPERIMENT),
    (0x06, lambda: True, [], REQUEST_TM_HEARTBEAT),
    (0x07, lambda: True, [], REQUEST_TM_HAL),
    (0x08, lambda: True, [], REQUEST_TM_STORAGE),
    (0x09, lambda: True, [], REQUEST_TM_PAYLOAD),
    (0x0A, lambda file_tag, requested_time: True, ["file_tag", "requested_time"], REQUEST_FILE_METADATA),
    (0x0B, lambda file_tag: True, ["file_tag"], REQUEST_FILE_PKT),
    (0x0C, lambda: True, [], REQUEST_IMAGE),
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
        # TODO build success response - ACK
    else:  # All other cases are errors
        # TODO build error response - Error messages
        pass
