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

from apps.command import commands as command_handlers
from apps.command import preconditions as precondition_handlers
from apps.comms.comms import SATELLITE_RADIO
from apps.comms.fifo import TransmitQueue
from apps.comms.modes import COMMS_MODE as COMMS_MODE_ID
from apps.telemetry.splat.splat.telemetry_codec import Ack
from apps.telemetry.splat.splat.telemetry_definition import COMMAND_IDS
from core import logger
from micropython import const

# Dispatch dictionaries are populated by decorators at import time.
COMMAND_DISPATCH = command_handlers.COMMAND_REGISTRY
PRECONDITION_DISPATCH = precondition_handlers.PRECONDITION_REGISTRY


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

    logger.info(f"Processing command: {satellite_func_name} with arguments: {argument_list}")
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
    """Push an ACK/NACK to the transmit queue, unless RF_STOP suppresses it."""
    command_id = response_args[0] if response_args else None
    in_rf_stop = SATELLITE_RADIO.get_comms_mode() == COMMS_MODE_ID.RF_STOP
    rf_resume_id = COMMAND_IDS["RF_RESUME"]

    if in_rf_stop and command_id != rf_resume_id:
        logger.warning("RF_STOP active: suppressing command ACK")
    else:
        ack = Ack(status, response_args)
        TransmitQueue.push_packet(ack)
        logger.info(f"Added ack obj to transmit queue: {ack}")

    if status == CommandProcessingStatus.COMMAND_EXECUTION_SUCCESS:
        logger.info("Command execution successful")

    else:
        logger.info(f"Command execution not successful due to error: {status}")
