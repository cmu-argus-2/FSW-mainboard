import pytest

from flight.apps.command.processor import COMMANDS, CommandProcessingStatus, process_command  # noqa F401


def mock_command_success(*args):
    return []


def mock_command_fail(*args):
    raise Exception("Mock execution failure")


@pytest.fixture
def setup_commands(monkeypatch):
    """Fixture to set up the COMMANDS list with mock commands."""

    mock_cmds = [
        (0x01, lambda: True, [], mock_command_success),  # Success command with no arguments
        (0x02, lambda: False, [], mock_command_success),  # Command with failed precondition
        (0x03, lambda: True, ["arg1"], mock_command_success),  # Command with one argument
        (0x04, lambda: True, [], mock_command_fail),  # Command that fails (raises an exception)
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
