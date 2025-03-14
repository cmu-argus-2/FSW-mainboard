from apps.command.constants import file_tags_str
from core.data_handler import DataHandler
from core.state_machine import STATES

""" Contains functions to check the preconditions of Commands """

_TIME_RANGE_LOW = 1577836800
_TIME_RANGE_HIGH = 1893456000


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

    if not isinstance(time_reference, int):
        return False

    """
    Since CPy time.time() starts on Jan 1st 2020,
    limit the time reference to at least this date.

    Can also update this to be our launch date,
    although that will lead to issues in testing
    while in development.
    """

    # Check that the timestamp is above Jan 1st 2020 UTC
    # Check that the timestamp is below Jan 1st 2030 UTC
    if 1577836800 < time_reference < 1893456000:
        return True
    else:
        return False


def file_id_exists(*args) -> bool:
    """
    Precondition for REQUEST_FILE_METADATA command.
    Checks that it is a valid file id that is mapped to a tag and that the file tag exists as a data process.
    """
    file_id = args[0]

    return (file_id in file_tags_str) and (DataHandler.data_process_exists(file_tags_str[file_id]))


# TODO: add a precondition for OD experiment (no OD should be in progress)
