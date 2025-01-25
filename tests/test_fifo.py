import pytest

from flight.apps.command.fifo import CommandQueue, QUEUE_STATUS


@pytest.fixture
def setup_queue():
    """Fixture to reset the CommandQueue before each test."""
    CommandQueue._queue = []
    CommandQueue.configure(max_size=5)  # Set a small max size for testing
    return CommandQueue


@pytest.fixture
def setup_single_element_queue():
    """Fixture to reset the CommandQueue before each test of a single element queue."""
    CommandQueue._queue = []
    CommandQueue.configure(max_size=1)
    return CommandQueue


def test_push_command_success(setup_queue):
    queue = setup_queue
    result = queue.push_command(0x01, ["arg1"])
    assert result == QUEUE_STATUS.OK
    assert queue.get_size() == 1


def test_push_command_overflow(setup_queue):
    queue = setup_queue
    for i in range(5):  # Fill the queue to its max size
        queue.push_command(i, [f"arg{i}"])
    result = queue.push_command(0x06, ["overflow_arg"])
    assert result == QUEUE_STATUS.OVERFLOW
    assert queue.get_size() == 5


def test_pop_command_success(setup_queue):
    queue = setup_queue
    queue.push_command(0x01, ["arg1"])
    cmd, status = queue.pop_command()
    assert status == QUEUE_STATUS.OK
    assert cmd == (0x01, ["arg1"])
    assert queue.is_empty()


def test_pop_command_empty(setup_queue):
    queue = setup_queue
    cmd, status = queue.pop_command()
    assert status == QUEUE_STATUS.EMPTY
    assert cmd is None


def test_is_empty(setup_queue):
    queue = setup_queue
    assert queue.is_empty()
    queue.push_command(0x01, ["arg1"])
    assert not queue.is_empty()


def test_is_full(setup_queue):
    queue = setup_queue
    for i in range(5):
        queue.push_command(i, [f"arg{i}"])
    assert queue.is_full()
    queue.pop_command()
    assert not queue.is_full()


def test_command_available(setup_queue):
    queue = setup_queue
    assert not queue.command_available()
    queue.push_command(0x01, ["arg1"])
    assert queue.command_available()


def test_overwrite_command(setup_single_element_queue):
    queue = setup_single_element_queue
    queue.overwrite_command(0x01, ["arg1"])
    assert queue.get_size() == 1
    queue.overwrite_command(0x02, ["arg2"])
    assert queue.get_size() == 1
    cmd, status = queue.pop_command()
    assert status == QUEUE_STATUS.OK
    assert cmd == (0x02, ["arg2"])
