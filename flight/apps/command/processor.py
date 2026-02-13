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
)
from apps.command.preconditions import file_id_exists, valid_inputs, valid_state, valid_time_format
from apps.comms.fifo import QUEUE_STATUS, TransmitQueue
from apps.telemetry.splat.splat.telemetry_codec import Ack, pack
from core import logger
from micropython import const

# See commands.py for function definitions (command functions and eventual preconditions)
# A command is defined as a tuple with the following elements:
# - ID: A unique identifier for the command
# - Precondition: A function that checks if the command can be executed
# - Arguments: A list of parameters that the command accepts
# - Execute: The function that executes the command



class CommandProcessingStatus:
    COMMAND_EXECUTION_SUCCESS = const(0x00)
    UNKNOWN_COMMAND_ID = const(0x01)
    PRECONDITION_FAILED = const(0x02)
    ARGUMENT_COUNT_MISMATCH = const(0x03)
    COMMAND_EXECUTION_FAILED = const(0x04)
    ARGUMENT_UNPACKING_FAILED = const(0x05)


def process_command(command):
    """Processes a command by ID and arguments, with lightweight validation and execution."""
    precondition = command.precondition
    satellite_func = command.satellite_func
    argument_list = command.get_arguments_list()
    logger.info(f"Processing command: {satellite_func} with arguments: {argument_list} and precondition: {precondition}")

    # Verify precondition
    # if not precondition(*args):
    try:
        if precondition is not None and not eval(precondition)(*argument_list):   # precondition None = no precondition for the command
            logger.error("Cmd: Precondition failed")
            return CommandProcessingStatus.PRECONDITION_FAILED, [command.command_id]
    except Exception as e:
        logger.error(f"Cmd: Precondition check failed with error: {e}")
        return CommandProcessingStatus.PRECONDITION_FAILED, [command.command_id]
    
    # [check] - should I check argument 

    # Execute the command function with arguments
    try:
        # response_args = execute(*args)
        logger.info(f"Executing command function: {satellite_func}")
        response_args = eval(satellite_func)(*argument_list)
        return CommandProcessingStatus.COMMAND_EXECUTION_SUCCESS, [command.command_id] + response_args
    except Exception as e:
        logger.error(f"Cmd: Command execution failed: {e}")
        # Optionally log stack trace to a file for deeper diagnostics
        return CommandProcessingStatus.COMMAND_EXECUTION_FAILED, [command.command_id]
    
    logger.warning("Cmd: Unknown command ID")
    return CommandProcessingStatus.UNKNOWN_COMMAND_ID, [command.command_id]


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

