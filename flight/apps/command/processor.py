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
    DOWNLINK_ALL,
    EVAL_STRING_COMMAND,
    FORCE_REBOOT,
    REQUEST_FILE_METADATA,
    REQUEST_FILE_PKT,
    REQUEST_IMAGE,
    REQUEST_TM_HAL,
    REQUEST_TM_NOMINAL,
    REQUEST_TM_PAYLOAD,
    REQUEST_TM_STORAGE,
    SCHEDULE_OD_EXPERIMENT,
    SUM,
    SWITCH_TO_STATE,
    TURN_OFF_PAYLOAD,
    UPLINK_TIME_REFERENCE,
    CREATE_TRANS,
    INIT_TRANS,
    GENERATE_ALL_PACKETS,
    GENERATE_X_PACKETS,
    GET_SINGLE_PACKET,
    TRANS_PAYLOAD
)
from apps.command.preconditions import file_id_exists, valid_inputs, valid_state, valid_time_format
from apps.comms.fifo import TransmitQueue
from apps.telemetry.splat.splat.telemetry_codec import Ack, pack
from core import logger
from micropython import const

# --- DISPATCH TABLES ---
# These dictionaries map the string names of functions to the actual function objects.
# avoid using the eval function to execute commands

COMMAND_DISPATCH = {
    "DOWNLINK_ALL": DOWNLINK_ALL,
    "EVAL_STRING_COMMAND": EVAL_STRING_COMMAND,
    "FORCE_REBOOT": FORCE_REBOOT,
    "REQUEST_FILE_METADATA": REQUEST_FILE_METADATA,
    "REQUEST_FILE_PKT": REQUEST_FILE_PKT,
    "REQUEST_IMAGE": REQUEST_IMAGE,
    "REQUEST_TM_HAL": REQUEST_TM_HAL,
    "REQUEST_TM_NOMINAL": REQUEST_TM_NOMINAL,
    "REQUEST_TM_PAYLOAD": REQUEST_TM_PAYLOAD,
    "REQUEST_TM_STORAGE": REQUEST_TM_STORAGE,
    "SCHEDULE_OD_EXPERIMENT": SCHEDULE_OD_EXPERIMENT,
    "SUM": SUM,
    "SWITCH_TO_STATE": SWITCH_TO_STATE,
    "TURN_OFF_PAYLOAD": TURN_OFF_PAYLOAD,
    "UPLINK_TIME_REFERENCE": UPLINK_TIME_REFERENCE,
    "CREATE_TRANS": CREATE_TRANS,
    "INIT_TRANS": INIT_TRANS,
    "GENERATE_ALL_PACKETS": GENERATE_ALL_PACKETS,
    "GENERATE_X_PACKETS": GENERATE_X_PACKETS,
    "GET_SINGLE_PACKET": GET_SINGLE_PACKET,
    "TRANS_PAYLOAD": TRANS_PAYLOAD
}

PRECONDITION_DISPATCH = {
    "file_id_exists": file_id_exists,
    "valid_inputs": valid_inputs,
    "valid_state": valid_state,
    "valid_time_format": valid_time_format,
}


class CommandProcessingStatus:
    COMMAND_EXECUTION_SUCCESS = const(0x00)
    UNKNOWN_COMMAND_ID = const(0x01)
    PRECONDITION_FAILED = const(0x02)
    ARGUMENT_COUNT_MISMATCH = const(0x03)
    COMMAND_EXECUTION_FAILED = const(0x04)
    ARGUMENT_UNPACKING_FAILED = const(0x05)


def process_command(command):
    """Processes a command by ID and arguments, with lightweight validation and execution."""
    precondition_name = command.precondition
    satellite_func_name = command.satellite_func
    argument_list = command.get_arguments_list()

    logger.info(
        f"Processing command: {satellite_func_name} with arguments: {argument_list}")
    logger.info(f"and precondition: {precondition_name}")

    # 1. Verify Precondition
    if precondition_name is not None:
        # Look up the precondition function in the dispatch table
        precondition_func = PRECONDITION_DISPATCH.get(precondition_name)

        if precondition_func is None:
            logger.error(f"Cmd: Unknown precondition '{precondition_name}'")
            return CommandProcessingStatus.PRECONDITION_FAILED, [command.command_id]

        try:
            # Execute the precondition function
            if not precondition_func(*argument_list):
                logger.error("Cmd: Precondition failed")
                return CommandProcessingStatus.PRECONDITION_FAILED, [command.command_id]
        except Exception as e:
            logger.error(f"Cmd: Precondition check failed with error: {e}")
            return CommandProcessingStatus.PRECONDITION_FAILED, [command.command_id]

    # 2. Execute the Command
    # Look up the command function in the dispatch table
    satellite_func = COMMAND_DISPATCH.get(satellite_func_name)

    if satellite_func is None:
        logger.warning(f"Cmd: Unknown command ID '{satellite_func_name}'")
        return CommandProcessingStatus.UNKNOWN_COMMAND_ID, [command.command_id]

    try:
        logger.info(f"Executing command function: {satellite_func_name}")
        # Execute the command function directly
        response_args = satellite_func(*argument_list)

        # Ensure response_args is a list/tuple before adding to list
        if response_args is None:
            response_args = []
        elif not isinstance(response_args, (list, tuple)):
            response_args = [response_args]

        return (
            CommandProcessingStatus.COMMAND_EXECUTION_SUCCESS,
            [command.command_id] + list(response_args),
        )

    except Exception as e:
        logger.error(f"Cmd: Command execution failed: {e}")
        # Optionally log stack trace to a file for deeper diagnostics
        return CommandProcessingStatus.COMMAND_EXECUTION_FAILED, [command.command_id]


def handle_command_execution_status(status, response_args):
    # If the command execution was successful, send a success response to Comms via Response Queue
    # If the command execution failed, send an error response with the error code to Comms via Response Queue

    # add ack response to transmit queue for comms to pick up and send to ground station
    # this is not the best place to do this, not sure where the best place to do this is
    ack = Ack(status, response_args)
    packed_ack = pack(ack)
    TransmitQueue.push_packet(packed_ack)
    logger.info(f"Added ack packet to transmit queue: {packed_ack}")

    if status == CommandProcessingStatus.COMMAND_EXECUTION_SUCCESS:
        logger.info("Command execution successful")

    else:  # All other cases are errors
        # TODO build more detailed error response - Error messages
        logger.info(f"Command execution not successful due to error: {status}")
        pass
