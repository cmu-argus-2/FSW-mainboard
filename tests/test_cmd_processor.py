import time

import pytest
from micropython import const

from flight.apps.command.constants import CMD_ID
from flight.apps.command.preconditions import valid_state, valid_time_format
from flight.apps.command.processor import process_command  # noqa F401
from flight.apps.command.processor import CommandProcessingStatus, check_arguments_size, unpack_command_arguments
from flight.apps.telemetry.helpers import pack_signed_long_int, pack_unsigned_long_int
from flight.core.state_machine import STATES


class MOCK_ARGUMENTS:
    time_in_state = 20
    time_reference = int(time.time())
    pos = 150
    vel = 50


def mock_command_success(*args):
    return []


def mock_command_fail(*args):
    raise Exception("Mock execution failure")


@pytest.fixture
def setup_commands(monkeypatch):
    """Fixture to set up the COMMANDS list with mock commands."""
    switch_to_state_args = (STATES.DETUMBLING).to_bytes(1, "big") + (MOCK_ARGUMENTS.time_in_state).to_bytes(4, "big")
    uplink_time_ref_args = (MOCK_ARGUMENTS.time_reference).to_bytes(4, "big")
    uplink_orbit_ref_args = (
        (MOCK_ARGUMENTS.time_reference).to_bytes(4, "big")
        + (MOCK_ARGUMENTS.pos).to_bytes(4, "big")
        + (MOCK_ARGUMENTS.pos * 2).to_bytes(4, "big")
        + (MOCK_ARGUMENTS.pos * 3).to_bytes(4, "big")
        + (MOCK_ARGUMENTS.vel).to_bytes(4, "big")
        + (MOCK_ARGUMENTS.vel * 2).to_bytes(4, "big")
        + (MOCK_ARGUMENTS.vel * 3).to_bytes(4, "big")
    )

    mock_cmds = [
        (0x01, lambda: True, [], mock_command_success),  # Success command with no arguments
        (0x02, lambda: False, [], mock_command_success),  # Command with failed precondition
        (0x03, lambda: True, ["arg1"], mock_command_success),  # Command with one argument
        (0x04, lambda: True, [], mock_command_fail),  # Command that fails (raises an exception)
        (
            CMD_ID.SWITCH_TO_STATE,
            lambda: True,
            switch_to_state_args,
            mock_command_success,
        ),  # Mock SWTICH_TO_STATE Command with 2 arguments, mixed data types
        (
            CMD_ID.UPLINK_TIME_REFERENCE,
            lambda: True,
            uplink_time_ref_args,
            mock_command_success,
        ),  # Mock UPLINK_TIME_REFERENCE Command with 1 arguments
        (
            CMD_ID.UPLINK_ORBIT_REFERENCE,
            lambda: True,
            uplink_orbit_ref_args,
            mock_command_success,
        ),  # Mock UPLINK_ORBIT_REFERENCE Command with 7 arguments, mixed data types
    ]
    monkeypatch.setattr("flight.apps.command.processor.COMMANDS", mock_cmds)
    return mock_cmds


def test_process_command_success(setup_commands):
    cmd_id, precond, args, f = setup_commands[0]
    result, response_args = process_command(cmd_id, *args)
    assert result == CommandProcessingStatus.COMMAND_EXECUTION_SUCCESS
    assert response_args == [0x01]


def test_process_command_precondition_failed(setup_commands):
    cmd_id, precond, args, f = setup_commands[1]
    result, response_args = process_command(cmd_id, *args)
    assert result == CommandProcessingStatus.PRECONDITION_FAILED
    assert response_args == [0x02]


def test_process_command_argument_count_mismatch(setup_commands):
    cmd_id, precond, args, f = setup_commands[2]
    result, response_args = process_command(cmd_id)  # No arguments passed, but one is expected
    assert result == CommandProcessingStatus.ARGUMENT_COUNT_MISMATCH
    assert response_args == [0x03]


def test_process_command_execution_failed(setup_commands):
    cmd_id, precond, args, f = setup_commands[3]
    result, response_args = process_command(cmd_id, *args)
    assert result == CommandProcessingStatus.COMMAND_EXECUTION_FAILED
    assert response_args == [0x04]


def test_process_command_unknown_command(setup_commands):
    result, response_args = process_command(0xFF)  # Command ID not in COMMANDS
    assert result == CommandProcessingStatus.UNKNOWN_COMMAND_ID
    print(response_args)
    assert response_args == [0xFF]


def test_unpack_one_argument(setup_commands):
    one_arg = unpack_command_arguments(setup_commands[5][0], setup_commands[5][2])
    assert one_arg == [MOCK_ARGUMENTS.time_reference]


def test_unpack_two_arguments(setup_commands):
    two_args = unpack_command_arguments(setup_commands[4][0], setup_commands[4][2])
    assert two_args == [STATES.DETUMBLING, MOCK_ARGUMENTS.time_in_state]


def test_unpack_several_arguments(setup_commands):
    several_args = unpack_command_arguments(setup_commands[6][0], setup_commands[6][2])
    assert several_args == [
        MOCK_ARGUMENTS.time_reference,
        [
            MOCK_ARGUMENTS.pos,
            MOCK_ARGUMENTS.pos * 2,
            MOCK_ARGUMENTS.pos * 3,
            MOCK_ARGUMENTS.vel,
            MOCK_ARGUMENTS.vel * 2,
            MOCK_ARGUMENTS.vel * 3,
        ],
    ]


@pytest.mark.parametrize(
    "command_id, arguments, expected_outputs",
    [
        (CMD_ID.FORCE_REBOOT, bytearray(), True),
        (CMD_ID.FORCE_REBOOT, [(1).to_bytes(1, "big")], False),
        (CMD_ID.SWITCH_TO_STATE, ((1).to_bytes(1, "big") + pack_unsigned_long_int([10], 0)), True),
        (CMD_ID.UPLINK_TIME_REFERENCE, (pack_unsigned_long_int([1741539497], 0)), True),
        (CMD_ID.UPLINK_TIME_REFERENCE, bytearray(), False),
        (
            CMD_ID.UPLINK_TIME_REFERENCE,
            (pack_unsigned_long_int([1741539497], 0) + pack_unsigned_long_int([1741539497], 0)),
            False,
        ),
        (
            CMD_ID.UPLINK_ORBIT_REFERENCE,
            (
                pack_unsigned_long_int([1741539497], 0)
                + pack_signed_long_int([0], 0)
                + pack_signed_long_int([1], 0)
                + pack_signed_long_int([2], 0)
                + pack_signed_long_int([3], 0)
                + pack_signed_long_int([4], 0)
                + pack_signed_long_int([5], 0)
            ),
            True,
        ),
        (CMD_ID.UPLINK_ORBIT_REFERENCE, (), False),
        (
            CMD_ID.UPLINK_ORBIT_REFERENCE,
            (
                pack_unsigned_long_int([1741539497], 0)
                + pack_signed_long_int([0], 0)
                + pack_signed_long_int([1], 0)
                + pack_signed_long_int([2], 0)
                + pack_signed_long_int([3], 0)
                + pack_signed_long_int([4], 0)
                + pack_signed_long_int([5], 0)
                + pack_signed_long_int([6], 0)
            ),
            False,
        ),
        (
            CMD_ID.UPLINK_ORBIT_REFERENCE,
            (
                pack_unsigned_long_int([1741539497], 0)
                + pack_signed_long_int([0], 0)
                + pack_signed_long_int([1], 0)
                + pack_signed_long_int([6], 0)
            ),
            False,
        ),
        (CMD_ID.TURN_OFF_PAYLOAD, (), True),
        (CMD_ID.TURN_OFF_PAYLOAD, ((1).to_bytes(1, "big")), False),
        (CMD_ID.SCHEDULE_OD_EXPERIMENT, (), True),
        (CMD_ID.SCHEDULE_OD_EXPERIMENT, ((1).to_bytes(1, "big")), False),
        (CMD_ID.REQUEST_TM_NOMINAL, (), True),
        (CMD_ID.REQUEST_TM_NOMINAL, ((1).to_bytes(1, "big")), False),
        (CMD_ID.REQUEST_TM_HAL, (), True),
        (CMD_ID.REQUEST_TM_HAL, ((1).to_bytes(1, "big")), False),
        (CMD_ID.REQUEST_TM_STORAGE, (), True),
        (CMD_ID.REQUEST_TM_STORAGE, ((1).to_bytes(1, "big")), False),
        (CMD_ID.REQUEST_TM_PAYLOAD, (), True),
        (CMD_ID.REQUEST_TM_PAYLOAD, ((1).to_bytes(1, "big")), False),
        (CMD_ID.REQUEST_FILE_METADATA, ((1).to_bytes(1, "big") + pack_unsigned_long_int([10], 0)), True),
        (
            CMD_ID.REQUEST_FILE_METADATA,
            ((1).to_bytes(1, "big") + pack_unsigned_long_int([10], 0) + pack_unsigned_long_int([20], 0)),
            False,
        ),
        (CMD_ID.REQUEST_FILE_METADATA, (), False),
        (CMD_ID.REQUEST_FILE_PKT, ((1).to_bytes(1, "big") + pack_unsigned_long_int([10], 0)), True),
        (
            CMD_ID.REQUEST_FILE_PKT,
            ((1).to_bytes(1, "big") + pack_unsigned_long_int([10], 0) + pack_unsigned_long_int([20], 0)),
            False,
        ),
        (CMD_ID.REQUEST_FILE_PKT, (), False),
    ],
)
def test_argument_size_check(command_id, arguments, expected_outputs):
    assert check_arguments_size(command_id, arguments) == expected_outputs


def test_valid_time_format():
    # Test valid Unix
    assert valid_time_format(1709980800)
    assert valid_time_format(1700001234)
    assert valid_time_format(1739719846)
    assert valid_time_format(1699900000)
    assert valid_time_format(1589387500)

    # Test edge cases and failing
    assert not valid_time_format(0)  # outside of valid mission range
    assert not valid_time_format("not_a_timestamp")  # invalid type
    assert not valid_time_format(9223372036854775807)  # beyond time_t limits
    assert not valid_time_format(999999999999999999999999999999)  # far positive
    assert not valid_time_format(-999999999999999999999999999999)  # far negative
    assert not valid_time_format(None)


def test_valid_state():
    invalid_state = const(0x0A)

    # Checking that it detects invalid state
    assert not valid_state(invalid_state)

    # Checking that it detects all the valid states
    assert valid_state(STATES.STARTUP)
    assert valid_state(STATES.DETUMBLING)
    assert valid_state(STATES.NOMINAL)
    assert valid_state(STATES.EXPERIMENT)
    assert valid_state(STATES.LOW_POWER)
