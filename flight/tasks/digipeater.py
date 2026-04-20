"""Dedicated digipeater task.

Consumes raw RF packets from DigipeaterRxQueue (fed by COMMS),
validates AX.25 frame format, adds satellite callsign to the
repeater via-path, and transmits the modified frame directly.

Becuase the link margin is quite big and the footprint of the satellite is also big
We will change how this will be implemented to avoid congesting the network
Packets should be addressed directly to the satellite callsign
And to simplify the checks, it will only look that the satellite callsign is in the path
It will not check the overall validity of the packet (apart from the special header)
"""

import re

from apps.comms.comms import SATELLITE_RADIO
from apps.digipeater import DIGIPEATER_QUEUE_STATUS, DigipeaterRxQueue
from apps.digipeater.aprs import add_asterisk_packet, is_valid_lora_aprs_packet
from core import TemplateTask
from core.satellite_config import digipeater_config as CONFIG


class Task(TemplateTask):

    def __init__(self, id):
        super().__init__(id)
        self.name = "DIGI"

        self.max_rx_queue = int(getattr(CONFIG, "RX_QUEUE_MAX", 20))

        # create the RE to find satellite CS in the path
        self._satellite_cs_re = re.compile(f"{SATELLITE_RADIO.SC_CALLSIGN}")

        DigipeaterRxQueue.configure(self.max_rx_queue)

    async def main_task(self):

        # print digipeater status
        self.log_info(f"RX queue: {DigipeaterRxQueue.get_size()}")

        while DigipeaterRxQueue.packet_available():
            raw_packet, status = DigipeaterRxQueue.pop_packet()
            self.log_info(f"Looking at packet: {raw_packet[:20]}")

            if status != DIGIPEATER_QUEUE_STATUS.OK or raw_packet is None:
                return

            # Validate LoRa APRS packet header and structure
            result = is_valid_lora_aprs_packet(raw_packet, self._satellite_cs_re)
            if not result == 6:
                self.log_warning(f"  Invalid packet format, dropping {result}")
                continue

            # Add asterik to callsign to indicate digipeating
            final_packet = add_asterisk_packet(raw_packet, self._satellite_cs_re)

            # Transmit directly (not via TransmitQueue, which applies SPLAT packing)
            if not SATELLITE_RADIO.transmit_message(final_packet):
                self.log_warning("Digipeater TX failed (RF_STOP or radio unavailable)")
