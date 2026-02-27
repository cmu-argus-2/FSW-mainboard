"""Dedicated digipeater task.

Consumes RX frames from DigipeaterRxQueue (fed by COMMS), applies relay policy,
and enqueues selected packets into TransmitQueue.
"""

from apps.comms.comms import SATELLITE_RADIO
from apps.comms.fifo import QUEUE_STATUS, TransmitQueue
from apps.comms.modes import COMMS_MODE
from apps.digipeater import DIGIPEATER_QUEUE_STATUS, DigipeaterRxQueue
from core import TemplateTask
from core.satellite_config import digipeater_config as CONFIG
from core.time_processor import TimeProcessor as TPM


class Task(TemplateTask):

    def __init__(self, id):
        super().__init__(id)
        self.name = "DIGI"

        # Compile-time feature gate. Runtime activation is COMMS_MODE.DIGIPEAT.
        self.enabled = bool(getattr(CONFIG, "ENABLED", True))
        self.forward_commands = bool(getattr(CONFIG, "FORWARD_COMMANDS", False))
        self.duplicate_window_s = int(getattr(CONFIG, "DUPLICATE_WINDOW_S", 30))
        self.max_rx_queue = int(getattr(CONFIG, "RX_QUEUE_MAX", 20))

        DigipeaterRxQueue.configure(self.max_rx_queue)

        # (fingerprint, expiry_time)
        self._recent = []

    @staticmethod
    def _fingerprint(data):
        # 32-bit FNV-1a hash
        h = 0x811C9DC5
        for b in data:
            h ^= b
            h = (h * 0x01000193) & 0xFFFFFFFF
        return h

    def _prune_recent(self, now):
        self._recent = [(fp, exp) for fp, exp in self._recent if exp > now]

    def _seen_recently(self, frame_bytes, now):
        fp = self._fingerprint(frame_bytes)

        for known_fp, exp in self._recent:
            if known_fp == fp and exp > now:
                return True

        self._recent.append((fp, now + self.duplicate_window_s))
        return False

    def _should_forward(self, frame):
        raw_packet = frame.get("raw_packet")
        if not raw_packet or len(raw_packet) < 2:
            return False

        source_header = frame.get("source_header")
        if source_header == SATELLITE_RADIO.ARGUS_CS:
            # Do not relay our own packets if they are overheard.
            return False

        if frame.get("is_command", False) and not self.forward_commands:
            return False

        return True

    def _queue_for_transmit(self, frame):
        raw_packet = frame["raw_packet"]
        relay_payload = raw_packet[1:]  # transmit_message() prepends this SAT's source header.

        status = TransmitQueue.push_packet(relay_payload)
        if status != QUEUE_STATUS.OK:
            self.log_warning(f"Digipeater TX queue push failed: {status}")

    async def main_task(self):
        now = TPM.time()
        self._prune_recent(now)
        mode_active = SATELLITE_RADIO.get_comms_mode() == COMMS_MODE.DIGIPEAT

        while DigipeaterRxQueue.frame_available():
            frame, status = DigipeaterRxQueue.pop_frame()
            if status != DIGIPEATER_QUEUE_STATUS.OK or frame is None:
                return

            # Drain queue even when disabled, to avoid stale buildup.
            if (not self.enabled) or (not mode_active):
                continue

            if not self._should_forward(frame):
                continue

            raw_packet = frame["raw_packet"]
            if self._seen_recently(raw_packet, now):
                continue

            self._queue_for_transmit(frame)
