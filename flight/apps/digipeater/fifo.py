"""Digipeater RX queue."""

from micropython import const


class DIGIPEATER_QUEUE_STATUS:
    OK = const(0)
    OVERFLOW = const(1)
    EMPTY = const(2)


class DigipeaterRxQueue:
    """FIFO queue holding received RF frames for the digipeater task."""

    _queue = []
    _max_size = 20

    @classmethod
    def configure(cls, max_size):
        cls._max_size = max_size

    @classmethod
    def push_frame(cls, frame):
        if len(cls._queue) < cls._max_size:
            cls._queue.append(frame)
            return DIGIPEATER_QUEUE_STATUS.OK
        return DIGIPEATER_QUEUE_STATUS.OVERFLOW

    @classmethod
    def pop_frame(cls):
        if cls._queue:
            return cls._queue.pop(0), DIGIPEATER_QUEUE_STATUS.OK
        return None, DIGIPEATER_QUEUE_STATUS.EMPTY

    @classmethod
    def frame_available(cls):
        return len(cls._queue) > 0

    @classmethod
    def get_size(cls):
        return len(cls._queue)

    @classmethod
    def clear(cls):
        cls._queue = []
