"""Digipeater app package."""

from apps.digipeater.fifo import DIGIPEATER_QUEUE_STATUS, DigipeaterRxQueue
from core import state_manager as SM
from core.states import STATES, TASK


class DigipeaterState:
    """Independent activation state for the digipeater subsystem."""

    active = False

    @classmethod
    def activate(cls):

        # check to see if we are in nominal mode
        if SM.current_state != STATES.NOMINAL:
            return ["invalid_state_for_digipeater_activation"]

        cls.active = True

        # Valid packets received while the digipeater is disabled
        # will be inserted into the queue, and transmitted once its
        # activated. This will clear the packets on init
        DigipeaterRxQueue.clear()

        task = SM.scheduled_tasks.get(TASK.DIGIPEATER)
        if task is None:
            return ["digipeater_task_not_scheduled"]

        task.start()
        return ["digipeater_activated"]

    @classmethod
    def deactivate(cls):
        cls.active = False

        task = SM.scheduled_tasks.get(TASK.DIGIPEATER)
        if task is None:
            return ["digipeater_task_not_scheduled"]

        task.stop()
        return ["digipeater_deactivated"]

    @classmethod
    def is_active(cls):
        return cls.active


__all__ = ["DIGIPEATER_QUEUE_STATUS", "DigipeaterRxQueue", "DigipeaterState"]
