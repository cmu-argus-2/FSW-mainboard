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
from apps.telemetry import TelemetryPacker
from core import logger
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STR_STATES
from core.time_processor import TimeProcessor as TPM

# from hal.configuration import SATELLITE
from ulab import numpy as np

FILE_PKTSIZE = 240


def FORCE_REBOOT():
    """Forces a power cycle of the spacecraft."""
    logger.info("Executing FORCE_REBOOT")
    supervisor.reload()
    # https://learn.adafruit.com/circuitpython-essentials/circuitpython-resetting
    return []


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


def UPLINK_ORBIT_REFERENCE(time_reference, orbital_parameters):
    """Sends time-referenced orbital information to update the orbit reference."""
    # TODO: Now that AD is gone, delete this command
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
    packed = TelemetryPacker.pack_tm_heartbeat()
    if packed:
        logger.info("Telemetry nominal packed")

    # Change message ID to nominal - differentiate between SAT_HEARTBEAT
    TelemetryPacker.change_tm_id_nominal()
    # Return TX message header
    return [get_tx_message_header()]


def REQUEST_TM_HAL():
    """Requests hardware-focused telemetry, including information on HAL, EPS, and errors."""
    logger.info("Executing REQUEST_TM_HAL")
    # Pack telemetry
    packed = TelemetryPacker.pack_tm_hal()
    if packed:
        logger.info("Telemetry hal packed")

    # Return TX message header
    return [get_tx_message_header()]


def REQUEST_TM_STORAGE():
    """Requests full storage status of the mainboard, including details on onboard processes."""
    logger.info("Executing REQUEST_TM_STORAGE")
    # Pack telemetry
    packed = TelemetryPacker.pack_tm_storage()
    if packed:
        logger.info("Telemetry storage packed")

    # Return TX message header
    return [get_tx_message_header()]


def REQUEST_TM_PAYLOAD():
    """Requests telemetry data from the payload, provided it is on."""
    logger.info("Executing REQUEST_TM_PAYLOAD")
    # Pack telemetry
    packed = TelemetryPacker.pack_tm_payload()
    if packed:
        logger.info("Telemetry payload packed")

    # Return TX message header
    return [get_tx_message_header()]


def REQUEST_FILE_METADATA(file_id, file_time=None):
    """Requests metadata for a specific file from the spacecraft."""
    logger.info(f"Executing REQUEST_FILE_METADATA with file_tag: {file_id} and file_time: {file_time}")
    file_path = None
    file_tag = file_tags_str[file_id]

    if file_time is None:
        file_path = DH.request_TM_path(file_tag)
    else:
        file_path = DH.request_TM_path(file_tag, file_time)

    return [file_path]


def REQUEST_FILE_PKT(file_id, file_time):
    """Requests a specific file packet from the spacecraft."""
    logger.info(f"Executing REQUEST_FILE_PKT with file_tag: {file_id}, file_tim: {file_time}")
    # TODO: potentially change if we want to handle file packets here instead of Comms
    file_path = None
    file_tag = file_tags_str[file_id]

    if file_time is None:
        file_path = DH.request_TM_path(file_tag)
    else:
        file_path = DH.request_TM_path(file_tag, file_time)

    return [file_path]


def REQUEST_IMAGE():
    """Requests an image from the spacecraft's internal storage."""
    logger.info("Executing REQUEST_IMAGE")
    # TODO: finish implementation, if we are keeping this command
    path = DH.request_TM_path_image()
    return [path]


def DOWNLINK_ALL():
    """Requests all files, images, and mission data be downlinked immediately in the event mission is compromised"""
    logger.info("Executing DOWNLINK_ALL")
    return [DH.get_all_data_processes_name()]


def get_tx_message_header():
    """ " Helper function to obtain the tx message header to send back"""
    return int.from_bytes(TelemetryPacker.FRAME()[0:1], "big")
