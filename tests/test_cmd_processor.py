import time

import pytest
from micropython import const

# Setup CircuitPython mocks for testing
import tests.cp_mock  # noqa: F401
from flight.apps.command.constants import CMD_ID
from flight.apps.command.preconditions import valid_state, valid_time_format
from flight.apps.command.processor import CommandProcessingStatus, process_command
from flight.core.state_machine import STATES


class MOCK_ARGUMENTS:
    time_in_state = 20
    time_reference = int(time.time())


def mock_command_success(*args):
    return []


def mock_command_fail(*args):
    raise Exception("Mock execution failure")


class MockCommand:
    """Mock command object matching the new command structure."""

    def __init__(self, command_id, satellite_func, precondition=None, arguments=None):
        self.command_id = command_id
        self.satellite_func = satellite_func
        self.precondition = precondition
        self._arguments = arguments or []

    def get_arguments_list(self):
        return self._arguments


@pytest.fixture
def setup_commands(monkeypatch):
    """Fixture to set up mock commands for testing."""
    # Mock the command dispatch and precondition dispatch
    mock_dispatch = {
        "mock_command_success": mock_command_success,
        "mock_command_fail": mock_command_fail,
    }

    mock_precondition_dispatch = {
        "always_true": lambda *args: True,
        "always_false": lambda *args: False,
    }

    monkeypatch.setattr("flight.apps.command.processor.COMMAND_DISPATCH", mock_dispatch)
    monkeypatch.setattr("flight.apps.command.processor.PRECONDITION_DISPATCH", mock_precondition_dispatch)

    return {
        "mock_dispatch": mock_dispatch,
        "mock_precondition_dispatch": mock_precondition_dispatch,
    }


def test_process_command_success(setup_commands):
    cmd = MockCommand(command_id=0x01, satellite_func="mock_command_success", precondition=None, arguments=[])
    result, response_args = process_command(cmd)
    assert result == CommandProcessingStatus.COMMAND_EXECUTION_SUCCESS
    assert response_args == [0x01]


def test_process_command_precondition_failed(setup_commands):
    cmd = MockCommand(command_id=0x02, satellite_func="mock_command_success", precondition="always_false", arguments=[])
    result, response_args = process_command(cmd)
    assert result == CommandProcessingStatus.PRECONDITION_FAILED
    assert response_args == [0x02]


def test_process_command_execution_failed(setup_commands):
    cmd = MockCommand(command_id=0x04, satellite_func="mock_command_fail", precondition=None, arguments=[])
    result, response_args = process_command(cmd)
    assert result == CommandProcessingStatus.COMMAND_EXECUTION_FAILED
    assert response_args == [0x04]


def test_process_command_unknown_command(setup_commands):
    cmd = MockCommand(command_id=0xFF, satellite_func="unknown_function", precondition=None, arguments=[])
    result, response_args = process_command(cmd)
    assert result == CommandProcessingStatus.UNKNOWN_COMMAND_ID
    assert response_args == [0xFF]


def test_valid_time_format():
    # Test valid Unix timestamps
    assert valid_time_format(1709980800)
    assert valid_time_format(1700001234)
    assert valid_time_format(1739719846)
    assert valid_time_format(1699900000)
    assert valid_time_format(1589387500)

    # Test edge cases and failing cases
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
