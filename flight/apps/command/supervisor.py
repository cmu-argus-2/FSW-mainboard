"""
Command supervisor for deferred high-impact actions.

This module gates critical actions (RF stop and reboot) until:
1) at least one TX has occurred after the request, and
2) the transmit queue is empty.
"""

import supervisor
from apps.comms.comms import SATELLITE_RADIO
from apps.comms.fifo import TransmitQueue
from apps.comms.modes import COMMS_MODE
from core import logger
from micropython import const


class _PENDING_ACTION:
    NONE = const(0)
    RF_STOP = const(1)
    REBOOT = const(2)


class CommandSupervisor:
    _pending_action = _PENDING_ACTION.NONE
    _min_tx_count = 0

    @classmethod
    def _arm_pending_action(cls, action, require_ack_tx=True):
        cls._pending_action = action
        # If ACK is expected, ensure it has a chance to go out first.
        cls._min_tx_count = SATELLITE_RADIO.tx_packet_count + (1 if require_ack_tx else 0)

    @classmethod
    def request_rf_stop(cls):
        cls._arm_pending_action(_PENDING_ACTION.RF_STOP, require_ack_tx=True)
        logger.warning("[CMD_SUP] RF_STOP requested; waiting for ACK TX + queue drain")
        return True

    @classmethod
    def request_reboot(cls):
        # In RF_STOP mode, command ACKs are intentionally suppressed.
        expect_ack_tx = SATELLITE_RADIO.get_comms_mode() != COMMS_MODE.RF_STOP
        cls._arm_pending_action(_PENDING_ACTION.REBOOT, require_ack_tx=expect_ack_tx)
        logger.warning("[CMD_SUP] REBOOT requested; waiting for ACK TX + queue drain")
        return True

    @classmethod
    def cancel_pending_rf_stop(cls):
        if cls._pending_action == _PENDING_ACTION.RF_STOP:
            cls._pending_action = _PENDING_ACTION.NONE
            cls._min_tx_count = 0
            logger.warning("[CMD_SUP] Pending RF_STOP cancelled")

    @classmethod
    def has_pending_action(cls):
        return cls._pending_action != _PENDING_ACTION.NONE

    @classmethod
    def _ready_to_execute(cls):
        return SATELLITE_RADIO.tx_packet_count >= cls._min_tx_count and TransmitQueue.is_empty()

    @classmethod
    def process_pending_action(cls):
        if cls._pending_action == _PENDING_ACTION.NONE:
            return False

        if not cls._ready_to_execute():
            return False

        action = cls._pending_action
        cls._pending_action = _PENDING_ACTION.NONE
        cls._min_tx_count = 0

        if action == _PENDING_ACTION.RF_STOP:
            SATELLITE_RADIO.set_comms_mode(COMMS_MODE.RF_STOP)
            logger.warning("[CMD_SUP] RF_STOP latched")
            return True

        if action == _PENDING_ACTION.REBOOT:
            logger.warning("[CMD_SUP] Executing deferred reboot")
            supervisor.reload()
            return True

        return False
