"""Dedicated digipeater task.

Consumes raw RF packets from DigipeaterRxQueue (fed by COMMS),
validates AX.25 frame format, adds satellite callsign to the
repeater via-path, and transmits the modified frame directly.
"""

from apps.comms.comms import SATELLITE_RADIO
from apps.digipeater import DIGIPEATER_QUEUE_STATUS, DigipeaterRxQueue, DigipeaterState
from apps.digipeater.ax25 import add_digipeater_to_via_path, is_valid_ax25_frame
from core import TemplateTask
from core.satellite_config import digipeater_config as CONFIG
from core.time_processor import TimeProcessor as TPM


class Task(TemplateTask):

    def __init__(self, id):
        super().__init__(id)
        self.name = "DIGI"

        self.enabled = bool(getattr(CONFIG, "ENABLED", True))
        self.duplicate_window_s = int(getattr(CONFIG, "DUPLICATE_WINDOW_S", 30))
        self.max_rx_queue = int(getattr(CONFIG, "RX_QUEUE_MAX", 20))

        DigipeaterRxQueue.configure(self.max_rx_queue)

        # (fingerprint, expiry_time) for duplicate detection
        self._recent = []

    @staticmethod
    def _fingerprint(data):
        """32-bit FNV-1a hash for duplicate detection."""
        h = 0x811C9DC5
        for b in data:
            h ^= b
            h = (h * 0x01000193) & 0xFFFFFFFF
        return h

    def _prune_recent(self, now):
        self._recent = [(fp, exp) for fp, exp in self._recent if exp > now]

    def _seen_recently(self, packet_bytes, now):
        fp = self._fingerprint(packet_bytes)

        for known_fp, exp in self._recent:
            if known_fp == fp and exp > now:
                return True

        self._recent.append((fp, now + self.duplicate_window_s))
        return False

    async def main_task(self):
        now = TPM.time()
        self._prune_recent(now)

        while DigipeaterRxQueue.packet_available():
            raw_packet, status = DigipeaterRxQueue.pop_packet()
            if status != DIGIPEATER_QUEUE_STATUS.OK or raw_packet is None:
                return

            # Drain queue even when inactive to prevent stale buildup
            if not self.enabled or not DigipeaterState.is_active():
                continue

            # Validate AX.25 frame format (filters out non-AX.25 packets like SPLAT commands)
            if not is_valid_ax25_frame(raw_packet):
                continue

            if self._seen_recently(raw_packet, now):
                continue

            # Add satellite callsign to the repeater via-path
            modified_packet = add_digipeater_to_via_path(raw_packet, SATELLITE_RADIO.SC_CALLSIGN)
            if modified_packet is None:
                self.log_warning("Failed to modify AX.25 via-path, dropping packet")
                continue

            # Transmit directly (not via TransmitQueue, which applies SPLAT packing)
            if not SATELLITE_RADIO.transmit_message(modified_packet):
                self.log_warning("Digipeater TX failed (RF_STOP or radio unavailable)")
