"""

CommandQueue class provides a First-In-First-Out (FIFO) queue implementation with a fixed maximum size.
It includes methods to configure the queue size, push commands onto the queue, pop commands from the queue,
and check the queue's status (empty, full, current size).

There is no priority mechanism, so commands are processed in the order they are received.

Author: Ibrahima S. Sow

"""

from micropython import const


class QUEUE_STATUS:
    # Error codes
    OK = const(0)  # Error code indicating successful operation.
    OVERFLOW = const(1)  # Error code indicating the queue is full.
    EMPTY = const(2)  # Error code indicating the queue is empty.
    OVERWRITE = const(3)  # Error code indicating failure to overwrite a 1 element queue.


class CommandQueue:
    """First-In-First-Out (FIFO) queue implementation with a fixed maximum size."""

    """Interface from Comms to CDH for the commands"""

    _queue = []  # The list representing the queue.
    _max_size = 1  # The maximum size of the queue.

    @classmethod
    def configure(cls, max_size):
        """Configures the maximum size of the queue."""
        cls._max_size = max_size

    @classmethod
    def push_command(cls, cmd_id, args):
        """Pushes a command onto the queue if not full. Returns an error code."""
        if len(cls._queue) < cls._max_size:
            cls._queue.append((cmd_id, args))
            return QUEUE_STATUS.OK
        else:
            return QUEUE_STATUS.OVERFLOW

    @classmethod
    def pop_command(cls):
        """Pops the first command from the queue (FIFO). Returns the command or an error code."""
        if cls._queue:
            return cls._queue.pop(0), QUEUE_STATUS.OK  # Pops the first element (FIFO), returns (cmd_id, args), error code
        else:
            return None, QUEUE_STATUS.EMPTY

    @classmethod
    def overwrite_command(cls, cmd_id, args):
        """Overwrites the command in a 1 element queue. Returns an error code."""
        cls._queue = [(cmd_id, args)]

        if len(cls._queue) == 1:
            return QUEUE_STATUS.OK
        else:
            return QUEUE_STATUS.OVERWRITE

    @classmethod
    def command_available(cls):
        """Checks if a command is available in the queue."""
        return len(cls._queue) > 0

    @classmethod
    def is_empty(cls):
        """Checks if the queue is empty."""
        return len(cls._queue) == 0

    @classmethod
    def is_full(cls):
        """Checks if the queue is full."""
        return len(cls._queue) == cls._max_size

    @classmethod
    def get_size(cls):
        """Returns the current size of the queue."""
        return len(cls._queue)


class ResponseQueue:
    """First-In-First-Out (FIFO) queue implementation with a fixed maximum size."""

    """Interface from CDH to Comms for the command processing status (ACK / Error messages)"""

    _queue = []  # The list representing the queue.
    _max_size = 1  # The maximum size of the queue.

    @classmethod
    def configure(cls, max_size):
        """Configures the maximum size of the queue."""
        cls._max_size = max_size

    @classmethod
    def push_response(cls, cmd_id, args):
        """Pushes a command onto the queue if not full. Returns an error code."""
        if len(cls._queue) < cls._max_size:
            cls._queue.append((cmd_id, args))
            return QUEUE_STATUS.OK
        else:
            return QUEUE_STATUS.OVERFLOW

    @classmethod
    def pop_response(cls):
        """Pops the first command from the queue (FIFO). Returns the command or an error code."""
        if cls._queue:
            return cls._queue.pop(0), QUEUE_STATUS.OK  # Pops the first element (FIFO), returns (cmd_id, args), error code
        else:
            return None, QUEUE_STATUS.EMPTY

    @classmethod
    def overwrite_response(cls, cmd_id, args):
        """Overwrites the command in a 1 element queue. Returns an error code."""
        cls._queue = [(cmd_id, args)]

        if len(cls._queue) == 1:
            return QUEUE_STATUS.OK
        else:
            return QUEUE_STATUS.OVERWRITE

    @classmethod
    def response_available(cls):
        """Checks if a command is available in the queue."""
        return len(cls._queue) > 0

    @classmethod
    def is_empty(cls):
        """Checks if the queue is empty."""
        return len(cls._queue) == 0

    @classmethod
    def is_full(cls):
        """Checks if the queue is full."""
        return len(cls._queue) == cls._max_size

    @classmethod
    def get_size(cls):
        """Returns the current size of the queue."""
        return len(cls._queue)
