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

# Command definitions
COMMANDS = [
    # REQUEST_TELEMETRY (no precondition needed)
    (0x01, lambda: True, [], lambda args: REQUEST_TELEMETRY()),
    # STREAM_TELEMETRY (requires NOMINAL or DOWNLINK state)
    (0x02, lambda: SATELLITE.state in [STATES.NOMINAL, STATES.DOWNLINK], [], lambda args: STREAM_TELEMETRY()),
    # TODO Add additional command definitions here
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
