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
from apps.command.constants import CMD_ID
from core import logger

# See commands.py for function definitions (command functions and eventual preconditions)
# A command is defined as a tuple with the following elements:
# - ID: A unique identifier for the command
# - Precondition: A function that checks if the command can be executed
# - Arguments: A list of parameters that the command accepts
# - Execute: The function that executes the command

COMMANDS = [
    (CMD_ID.FORCE_REBOOT, lambda: True, [], FORCE_REBOOT),
    (CMD_ID.SWITCH_TO_STATE, lambda: True, ["target_state_id", "time_in_state"], SWITCH_TO_STATE),
    (CMD_ID.UPLINK_TIME_REFERENCE, lambda: True, ["time_in_state"], UPLINK_TIME_REFERENCE),
    (CMD_ID.UPLINK_ORBIT_REFERENCE, lambda: True, ["time_in_state", "orbital_parameters"], UPLINK_ORBIT_REFERENCE),
    (CMD_ID.TURN_OFF_PAYLOAD, lambda: True, [], TURN_OFF_PAYLOAD),
    (CMD_ID.SCHEDULE_OD_EXPERIMENT, lambda: True, [], SCHEDULE_OD_EXPERIMENT),
    (CMD_ID.REQUEST_TM_HEARTBEAT, lambda: True, [], REQUEST_TM_HEARTBEAT),
    (CMD_ID.REQUEST_TM_HAL, lambda: True, [], REQUEST_TM_HAL),
    (CMD_ID.REQUEST_TM_STORAGE, lambda: True, [], REQUEST_TM_STORAGE),
    (CMD_ID.REQUEST_TM_PAYLOAD, lambda: True, [], REQUEST_TM_PAYLOAD),
    (
        CMD_ID.REQUEST_FILE_METADATA,
        lambda file_tag, requested_time: True,
        ["file_tag", "requested_time"],
        REQUEST_FILE_METADATA,
    ),
    (CMD_ID.REQUEST_FILE_PKT, lambda file_tag: True, ["file_tag"], REQUEST_FILE_PKT),
    (CMD_ID.REQUEST_IMAGE, lambda: True, [], REQUEST_IMAGE),
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
        # TODO build success response - ACK

    else:  # All other cases are errors
        # TODO build error response - Error messages
        logger.info(f"Command execution not successful due to error: {status}")
        pass


def unpack_command_arguments(cmd_id, cmd_arglist):
    """This will unpack the command arguments received from Command Queue"""
    cmd_arglist = list(cmd_arglist)
    cmd_args = []
    # TODO Fill out for commands with file requests
    if cmd_id == CMD_ID.SWITCH_TO_STATE:
        cmd_args.append(cmd_arglist[0])  # target_state_id (uint8)
        cmd_args.append(tm_helper.unpack_unsigned_long_int(cmd_arglist[1:5]))  # time_in_state (uint32)

    elif cmd_id == CMD_ID.UPLINK_TIME_REFERENCE:
        cmd_args.append(tm_helper.unpack_unsigned_long_int(cmd_arglist[0:4]))  # time_in_state (uint32)

    elif cmd_id == CMD_ID.UPLINK_ORBIT_REFERENCE:
        cmd_args.append(tm_helper.unpack_unsigned_long_int(cmd_arglist[0:4]))  # time_in_state (uint32)
        cmd_args.append(tm_helper.unpack_signed_long_int(cmd_arglist[4:8]))  # pos_x (int32)
        cmd_args.append(tm_helper.unpack_signed_long_int(cmd_arglist[8:12]))  # pos_y (int32)
        cmd_args.append(tm_helper.unpack_signed_long_int(cmd_arglist[12:16]))  # pos_z (int32)
        cmd_args.append(tm_helper.unpack_signed_long_int(cmd_arglist[16:20]))  # vel_x (int32)
        cmd_args.append(tm_helper.unpack_signed_long_int(cmd_arglist[20:24]))  # vel_y (int32)
        cmd_args.append(tm_helper.unpack_signed_long_int(cmd_arglist[24:28]))  # vel_z (int32)

    else:
        # For all other commands with no arguments
        cmd_args = []

    logger.info(f"CMD_ID: {cmd_id} Argument List: {cmd_args}")
    return cmd_args
