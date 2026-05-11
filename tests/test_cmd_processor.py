import time

import pytest

# Setup CircuitPython mocks for testing
import tests.cp_mock  # noqa: F401
from flight.apps.command.processor import CommandProcessingStatus, process_command


class MOCK_ARGUMENTS:
    time_in_state = 20
    time_reference = int(time.time())


def mock_command_success(*args):
    return []


def mock_command_fail(*args):
    raise Exception("Mock execution failure")


class MockCommand:
    """Mock command object matching the new command structure."""

    def __init__(self, command_id, name, arguments=None):
        self.command_id = command_id
        self.name = name
        self._arguments = arguments or []

    def get_arguments_list(self):
        return self._arguments


@pytest.fixture
def setup_commands(monkeypatch):
    """Fixture to set up mock commands for testing."""
    # Mock the command dispatch for testing.
    mock_dispatch = {
        "mock_command_success": mock_command_success,
        "mock_command_fail": mock_command_fail,
    }

    monkeypatch.setattr("flight.apps.command.processor.COMMAND_DISPATCH", mock_dispatch)

    return {"mock_dispatch": mock_dispatch}


def test_process_command_success(setup_commands):
    cmd = MockCommand(command_id=0x01, name="mock_command_success", arguments=[])
    result, response_args = process_command(cmd)
    assert result == CommandProcessingStatus.COMMAND_EXECUTION_SUCCESS
    assert response_args == []


def test_process_command_execution_failed(setup_commands):
    cmd = MockCommand(command_id=0x04, name="mock_command_fail", arguments=[])
    result, response_args = process_command(cmd)
    assert result == CommandProcessingStatus.COMMAND_EXECUTION_FAILED
    assert response_args == []


def test_process_command_unknown_command(setup_commands):
    cmd = MockCommand(command_id=0xFF, name="unknown_function", arguments=[])
    result, response_args = process_command(cmd)
    assert result == CommandProcessingStatus.UNKNOWN_COMMAND_ID
    assert response_args == []
