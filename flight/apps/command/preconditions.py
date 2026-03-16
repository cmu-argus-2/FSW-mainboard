from apps.command.constants import file_tags_str
from core.data_handler import DataHandler
from core.state_machine import STATES

""" Contains functions to check the preconditions of Commands """

_TIME_RANGE_LOW = 1577836800
_TIME_RANGE_HIGH = 1893456000
PRECONDITION_REGISTRY = {}


def register_precondition(name=None):
    """Decorator to register a precondition function in PRECONDITION_REGISTRY."""

    def decorator(func):
        precondition_name = name or func.__name__
        PRECONDITION_REGISTRY[precondition_name] = func
        return func

    return decorator


@register_precondition()
def valid_inputs(*args) -> bool:
    """
    Precondition for SUM command.
    Checks that the inputs are integers or floats.
    """
    opA = args[0]
    opB = args[1]
    if (isinstance(opA, (int, float))) and (isinstance(opB, (int, float))):
        return True
    else:
        return False


@register_precondition()
def valid_state(*args) -> bool:
    """
    Precondition for SWITCH_TO_STATE command.
    Will check that the target_state_id is actually one of the states
    """
    target_state_id = args[0]
    return STATES.STARTUP <= target_state_id <= STATES.LOW_POWER


@register_precondition()
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
    if _TIME_RANGE_LOW < time_reference < _TIME_RANGE_HIGH:
        return True
    else:
        return False


@register_precondition()
def file_id_exists(*args) -> bool:
    """
    Precondition for REQUEST_FILE_METADATA command.
    Checks that it is a valid file id that is mapped to a tag and that the file tag exists as a data process.
    """
    file_id = args[0]

    return (file_id in file_tags_str) and (DataHandler.data_process_exists(file_tags_str[file_id]))


# TODO: add a precondition for OD experiment (no OD should be in progress)
