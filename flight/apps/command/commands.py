"""

Command Definitions

======================

This modules contains the definition of the command functions for the satellite.


Each command is defined as follows:
- ID: A unique identifier for the command.
- Name: A string representation of the command for debugging.
- Description: A brief description of the command.
- Arguments: A list of parameters that the command accepts.
- Precondition: A list of conditions that must be met before executing the command.

See the documentation for a full description of each command.

Author: Ibrahima S. Sow

"""

import supervisor
from apps.command.constants import file_tags_str
from apps.comms.fifo import QUEUE_STATUS, TransmitQueue
from apps.telemetry.middleware import Frame as TelemetryFrame  # this will substitute for the old telemetry packer
from core import logger
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STR_STATES
from core.time_processor import TimeProcessor as TPM

FILE_PKTSIZE = 240


def FORCE_REBOOT():
    """Forces a power cycle of the spacecraft."""
    logger.info("Executing FORCE_REBOOT")
    supervisor.reload()
    # https://learn.adafruit.com/circuitpython-essentials/circuitpython-resetting
    return []

def SUM(opA, opB):
    """
    Test command
    used to experiment addining new command and testing the arguments 
    """
    logger.info(f"Executing SUM with opA: {opA} and opB: {opB}")
    return [opA + opB]
    

def SWITCH_TO_STATE(target_state_id, time_in_state=None):
    """Forces a switch of the spacecraft to a specific state."""
    logger.info(f"Executing SWITCH_TO_STATE with target_state: {STR_STATES[target_state_id]}, time_in_state: {time_in_state}")
    SM.start_forced_state(target_state_id, time_in_state)
    return []


def UPLINK_TIME_REFERENCE(time_reference):
    """Sends a time reference to the spacecraft to update the time processing module."""
    logger.info(f"Executing UPLINK_TIME_REFERENCE with current_time: {time_reference}")
    TPM.set_time(time_reference)
    return []


def TURN_OFF_PAYLOAD():
    """Sends a shutdown command to the payload and turns off its power line."""
    logger.info("Executing TURN_OFF_PAYLOAD")
    return []


def SCHEDULE_OD_EXPERIMENT():
    """Schedules an orbit determination experiment at the next available opportunity."""
    logger.info("Executing SCHEDULE_OD_EXPERIMENT")
    return []


def REQUEST_TM_NOMINAL():
    """Requests a nominal snapshot of all subsystems."""
    logger.info("Executing REQUEST_TM_NOMINAL")
    # Pack telemetry
    packet = TelemetryFrame.pack_tm_heartbeat()#
    TransmitQueue.push_packet(packet)
    logger.info("Telemetry nominal packed and pushed to transmit queue")
        
    # might be interesting to differentiate between periodic hearbeats
    # might want to add that this is a response

    return []


def REQUEST_TM_HAL():
    """Requests hardware-focused telemetry, including information on HAL, EPS, and errors."""
    logger.info("Executing REQUEST_TM_HAL")
    # Pack telemetry
    packet = TelemetryFrame.pack_tm_hal()
    TransmitQueue.push_packet(packet)
    logger.info("Telemetry hal packed and pushed to transmit queue")

    return []


def REQUEST_TM_STORAGE():
    """Requests full storage status of the mainboard, including details on onboard processes."""
    logger.info("Executing REQUEST_TM_STORAGE")
    # Pack telemetry
    packet = TelemetryFrame.pack_tm_storage()
    TransmitQueue.push_packet(packet)
    logger.info("Telemetry storage packed and pushed to transmit queue")

    return []


def REQUEST_TM_PAYLOAD():
    """Requests telemetry data from the payload, provided it is on."""
    logger.info("Executing REQUEST_TM_PAYLOAD")
    # Pack telemetry
    packet = TelemetryFrame.pack_tm_payload()
    TransmitQueue.push_packet(packet)
    logger.info("Telemetry payload packed and pushed to transmit queue")

    return []


def REQUEST_FILE_METADATA(file_id, file_time=None):
    """Requests metadata for a specific file from the spacecraft."""
    logger.info(f"Executing REQUEST_FILE_METADATA with file_tag: {file_id} and file_time: {file_time}")
    file_path = None
    file_tag = file_tags_str[file_id]

    if file_time is None or file_time == 0:
        # None or 0 means get the latest file
        file_path = DH.request_TM_path(file_tag, True)
    else:
        # Specify file_tag, latest = False and file_time
        file_path = DH.request_TM_path(file_tag, False, file_time)

    return [file_path]


# NOTE: REQUEST_FILE_PKT handled internally in comms
def REQUEST_FILE_PKT(file_id, file_time):
    raise NotImplementedError("Handled internally by comms subsystem")


def REQUEST_IMAGE():
    raise NotImplementedError("Not implemented")


def DOWNLINK_ALL(file_id, file_time=None):
    """Downlinks all packets for a specific file from the spacecraft."""
    logger.info(f"Executing DOWNLINK_ALL with file_tag: {file_id} and file_time: {file_time}")
    file_path = None
    file_tag = file_tags_str[file_id]

    if file_time is None or file_time == 0:
        # None or 0 means get the latest file
        file_path = DH.request_TM_path(file_tag)
    else:
        # Specify file_tag, latest = False and file_time
        file_path = DH.request_TM_path(file_tag, False, file_time)

    return [file_path]

def EVAL_STRING_COMMAND(string_command):
    """
    As of right now this is just for debugging purposes
    will receive a string, will eval it and return the results. """
    logger.info(f"Executing EVAL_STRING_COMMAND with request: {string_command}")

    try:
        result = eval(string_command)
        return [result]
    except Exception as e:
        logger.error(f"EVAL_STRING_COMMAND execution failed: {e}")
        return ["eval_string_command_failed"]


def get_tx_message_header():
    """ " Helper function to obtain the tx message header to send back"""
    return int.from_bytes(TelemetryFrame.FRAME()[0:1], "big")
