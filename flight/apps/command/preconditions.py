import time

from apps.command.constants import file_tags_str
from core.data_handler import DataHandler
from core.state_machine import STATES

""" Contains functions to check the preconditions of Commands """


def valid_state(*args) -> bool:
    """
    Precondition for SWITCH_TO_STATE command.
    Will check that the target_state_id is actually one of the states
    """
    target_state_id = args[0]
    return STATES.STARTUP <= target_state_id <= STATES.LOW_POWER


def valid_time_format(*args) -> bool:
    """
    Precondition for UPLINK_TIME_REFERENCE / UPLINK_ORBIT_TIME_REFERENCE commands.
    Will check that time is of proper UNIX format
    """
    time_reference = args[0]

    if time_reference < 3004213696:  # 40 years into the future
        return True
    return False

    # if time_reference is None:
    #     return False

    # try:
    #     # Try to convert it to a time struct will verify if it was of proper UNIX format
    #     time.gmtime(time_reference)
    #     return True
    # except (ValueError, TypeError, OverflowError, OSError):
    #     return False


def file_id_exists(*args) -> bool:
    """
    Precondition for REQUEST_FILE_METADATA command.
    Checks that it is a valid file id that is mapped to a tag and that the file tag exists as a data process.
    """
    file_id = args[0]

    return (file_id in file_tags_str) and (DataHandler.data_process_exists(file_tags_str[file_id]))


# TODO: add a precondition for OD experiment (no OD should be in progress)
