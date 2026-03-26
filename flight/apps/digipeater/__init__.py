"""Digipeater app package."""

from apps.digipeater.fifo import DIGIPEATER_QUEUE_STATUS, DigipeaterRxQueue


class DigipeaterState:
    """Independent activation state for the digipeater subsystem."""

    active = False

    @classmethod
    def activate(cls):
        cls.active = True

    @classmethod
    def deactivate(cls):
        cls.active = False

    @classmethod
    def is_active(cls):
        return cls.active


__all__ = ["DIGIPEATER_QUEUE_STATUS", "DigipeaterRxQueue", "DigipeaterState"]
