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

import apps.telemetry.helpers as tm_helper
from apps.command import ResponseQueue
from apps.command.commands import (
    DOWNLINK_ALL,
    FORCE_REBOOT,
    REQUEST_FILE_METADATA,
    REQUEST_FILE_PKT,
    REQUEST_IMAGE,
    REQUEST_TM_HAL,
    REQUEST_TM_NOMINAL,
    REQUEST_TM_PAYLOAD,
    REQUEST_TM_STORAGE,
    SCHEDULE_OD_EXPERIMENT,
    SWITCH_TO_STATE,
    TURN_OFF_PAYLOAD,
    UPLINK_TIME_REFERENCE,
)
from apps.command.constants import CMD_ID
from apps.command.preconditions import file_id_exists, valid_state, valid_time_format
from core import logger
from micropython import const

# See commands.py for function definitions (command functions and eventual preconditions)
# A command is defined as a tuple with the following elements:
# - ID: A unique identifier for the command
# - Precondition: A function that checks if the command can be executed
# - Arguments: A list of parameters that the command accepts
# - Execute: The function that executes the command

COMMANDS = [
    (CMD_ID.FORCE_REBOOT, lambda: True, [], FORCE_REBOOT),
    (CMD_ID.SWITCH_TO_STATE, valid_state, ["target_state_id", "time_in_state"], SWITCH_TO_STATE),
    (CMD_ID.UPLINK_TIME_REFERENCE, valid_time_format, ["time_reference"], UPLINK_TIME_REFERENCE),
    (CMD_ID.TURN_OFF_PAYLOAD, lambda: True, [], TURN_OFF_PAYLOAD),
    (CMD_ID.SCHEDULE_OD_EXPERIMENT, lambda: True, [], SCHEDULE_OD_EXPERIMENT),
    (CMD_ID.REQUEST_TM_NOMINAL, lambda: True, [], REQUEST_TM_NOMINAL),
    (CMD_ID.REQUEST_TM_HAL, lambda: True, [], REQUEST_TM_HAL),
    (CMD_ID.REQUEST_TM_STORAGE, lambda: True, [], REQUEST_TM_STORAGE),
    (CMD_ID.REQUEST_TM_PAYLOAD, lambda: True, [], REQUEST_TM_PAYLOAD),
    (
        CMD_ID.REQUEST_FILE_METADATA,
        file_id_exists,
        ["file_id", "file_time"],
        REQUEST_FILE_METADATA,
    ),
    (CMD_ID.REQUEST_FILE_PKT, file_id_exists, ["file_id", "file_time"], REQUEST_FILE_PKT),
    (CMD_ID.REQUEST_IMAGE, lambda: True, [], REQUEST_IMAGE),
    (CMD_ID.DOWNLINK_ALL, file_id_exists, ["file_id", "file_time"], DOWNLINK_ALL),
]


class CommandProcessingStatus:
    COMMAND_EXECUTION_SUCCESS = const(0x00)
    UNKNOWN_COMMAND_ID = const(0x01)
    PRECONDITION_FAILED = const(0x02)
    ARGUMENT_COUNT_MISMATCH = const(0x03)
    COMMAND_EXECUTION_FAILED = const(0x04)
    ARGUMENT_UNPACKING_FAILED = const(0x05)


def process_command(cmd_id, *args):
    """Processes a command by ID and arguments, with lightweight validation and execution."""
    for command in COMMANDS:
        if command[0] == cmd_id:
            precondition, arg_list, execute = command[1:]

            # Verify precondition
            if not precondition(*args):
                logger.error("Cmd: Precondition failed")
                return CommandProcessingStatus.PRECONDITION_FAILED, [cmd_id]

            # Verify the argument count
            if len(args) != len(arg_list):
                print(arg_list)
                logger.error(f"Cmd: Argument count mismatch for command ID {cmd_id}")
                return CommandProcessingStatus.ARGUMENT_COUNT_MISMATCH, [cmd_id]

            # Execute the command function with arguments
            try:
                response_args = execute(*args)
                return CommandProcessingStatus.COMMAND_EXECUTION_SUCCESS, [cmd_id] + response_args
            except Exception as e:
                logger.error(f"Cmd: Command execution failed: {e}")
                # Optionally log stack trace to a file for deeper diagnostics
                return CommandProcessingStatus.COMMAND_EXECUTION_FAILED, [cmd_id]

    logger.warning("Cmd: Unknown command ID")
    return CommandProcessingStatus.UNKNOWN_COMMAND_ID, [cmd_id]


def handle_command_execution_status(status, response_args):
    # If the command execution was successful, send a success response to Comms via Response Queue
    # If the command execution failed, send an error response with the error code to Comms via Response Queue

    ResponseQueue.overwrite_response(status, response_args)

    if status == CommandProcessingStatus.COMMAND_EXECUTION_SUCCESS:
        logger.info("Command execution successful")

    else:  # All other cases are errors
        # TODO build more detailed error response - Error messages
        logger.info(f"Command execution not successful due to error: {status}")
        pass


def check_arguments_size(cmd_id, cmd_arglist):
    """
    Checks that the payload size containing the command arguments are
    of the correct size that we expect
    """
    if CMD_ID.ARGS_LEN[cmd_id] != len(cmd_arglist):
        return False
    return True


def unpack_command_arguments(cmd_id, cmd_arglist):
    """This will unpack the command arguments received from Command Queue"""
    # TODO: Need to do error handling for unpacking

    cmd_arglist = list(cmd_arglist)
    cmd_args = []

    # Check that the payload is of the correct length
    if not check_arguments_size(cmd_id, cmd_arglist):
        logger.error(f"[COMMAND]: Incorrect payload size, expected: {CMD_ID.ARGS_LEN[cmd_id]}, received: {len(cmd_arglist)}")
        return CommandProcessingStatus.ARGUMENT_UNPACKING_FAILED

    if cmd_id == CMD_ID.SWITCH_TO_STATE or cmd_id == CMD_ID.REQUEST_FILE_METADATA or cmd_id == CMD_ID.DOWNLINK_ALL:
        cmd_args.append(cmd_arglist[0])  # target_state_id / file_id (uint8)
        cmd_args.append(tm_helper.unpack_unsigned_long_int(cmd_arglist[1:5]))  # time_in_state / file_time (uint32)

    elif cmd_id == CMD_ID.UPLINK_TIME_REFERENCE:
        cmd_args.append(tm_helper.unpack_unsigned_long_int(cmd_arglist[0:4]))  # time_reference (uint32)

    elif cmd_id == CMD_ID.REQUEST_FILE_PKT:
        cmd_args.append(cmd_arglist[0])  # file_id (uint8)
        cmd_args.append(tm_helper.unpack_unsigned_long_int(cmd_arglist[1:5]))  # file_time (uint32)

    else:
        # For all other commands with no arguments
        cmd_args = []

    if False in cmd_args:
        logger.error("[COMMAND] Command argument unpacking failed")
        return CommandProcessingStatus.ARGUMENT_UNPACKING_FAILED

    logger.info(f"[COMMAND] Unpacked arguments - CMD_ID: {cmd_id}, Argument List: {cmd_args}")
    return cmd_args
