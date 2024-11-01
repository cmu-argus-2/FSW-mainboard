"""

CommandQueue class provides a Last-In-First-Out (LIFO) queue implementation with a fixed maximum size.
It includes methods to configure the queue size, push commands onto the queue, pop commands from the queue,
and check the queue's status (empty, full, current size).

"""

from micropython import const


class CommandQueue:
    """Last-In-First-Out (LIFO) queue implementation with a fixed maximum size."""

    _queue = []  # The list representing the queue.
    _max_size = 10  # The maximum size of the queue.

    # Error codes
    OK = const(0)  # Error code indicating successful operation.
    OVERFLOW = const(1)  # Error code indicating the queue is full.
    EMPTY = const(2)  # Error code indicating the queue is empty.

    @classmethod
    def configure(cls, max_size=10):
        """Configures the maximum size of the queue."""
        cls._max_size = max_size

    @classmethod
    def push_command(cls, cmd, args):
        """Pushes a command onto the queue if not full. Returns an error code."""
        if len(cls._queue) < cls._max_size:
            cls._queue.append((cmd, args))
            return cls.OK
        else:
            return cls.OVERFLOW

    @classmethod
    def pop_command(cls):
        """Pops the last command from the queue (LIFO). Returns the command or an error code."""
        if cls._queue:
            return cls._queue.pop(), cls.OK
        else:
            return None, cls.EMPTY

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
