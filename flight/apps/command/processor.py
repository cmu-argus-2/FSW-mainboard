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
from apps.comms.fifo import TransmitQueue
from apps.telemetry.splat.splat.telemetry_codec import Ack
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
    # If the command execution was successful, send a success response to Comms via Response Queue
    # If the command execution failed, send an error response with the error code to Comms via Response Queue

    # add ack response to transmit queue for comms to pick up and send to ground station
    # this is not the best place to do this, not sure where the best place to do this is
    ack = Ack(status, response_args)
    TransmitQueue.push_packet(ack)
    logger.info(f"Added ack obj to transmit queue: {ack}")

    if status == CommandProcessingStatus.COMMAND_EXECUTION_SUCCESS:
        logger.info("Command execution successful")

    else:  # All other cases are errors
        # TODO build more detailed error response - Error messages
        logger.info(f"Command execution not successful due to error: {status}")
        pass
