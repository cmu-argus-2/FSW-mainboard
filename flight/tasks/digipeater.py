"""Dedicated digipeater task.

Consumes raw RF packets from DigipeaterRxQueue (fed by COMMS),
validates AX.25 frame format, adds satellite callsign to the
repeater via-path, and transmits the modified frame directly.

Becuase the link margin is quite big and the footprint of the satellite is also big
We will change how this will be implemented to avoid congesting the network
Packets should be addressed directly to the satellite callsign
And to simplify the checks, it will only look that the satellite callsign is in the path
It will not check the overall validity of the packet (apart from the special header)

TX ASCII: <ÿCS5CEP-1>APRS4;CT6xxx:ARGUS TEST MESSAGE
RX ASCII: <�CS5CEP-1>APRS4;CT6xxx*:ARGUS TEST MESSAGE

This is the current structure. For a message to be repeated, it will have to be addressed to the satellite
Overall format of the packet is not checked
    - checks the lora aprs special header
    - it has at least 20 characters
    - if data is ascii decodable
    - if satellite calsign is in the path
    - if the position of the callsign is in the first 20 characters of the string
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

        # Prefix (Bytes)
        prefix = "^(.*?)"
        # SRC (6 chars) - Wrapped in () so it becomes Group 2
        src = "([A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9])"
        # Suffix - Groups 3 & 4
        suffix = "(-(1[0-5]|[1-9]))?"
        # Separator - Group 5
        sep = "(>)"
        # DST - Group 6
        dst = "([A-Za-z0-9]+,)?"
        # Code - Group 7
        callsign = "(" + SATELLITE_RADIO.SC_CALLSIGN + ")"
        # Tail - Groups 8 & 9
        tail = "((,[^:]*)?:)"
        # Rest - Group 10
        rest = "(.*)"

        pattern = "^" + src + suffix + sep + \
            dst + callsign + tail

        pattern_with_rest = prefix + src + suffix + sep + \
            dst + callsign + tail + rest

        self._satellite_message_re = re.compile(pattern)
        self._satellite_replace_re = re.compile(pattern_with_rest)

        DigipeaterRxQueue.configure(self.max_rx_queue)

    async def main_task(self):

        # print digipeater status
        self.log_info(f"RX queue: {DigipeaterRxQueue.get_size()}")

        while DigipeaterRxQueue.packet_available():
            raw_packet, status = DigipeaterRxQueue.pop_packet()
            if status != DIGIPEATER_QUEUE_STATUS.OK or raw_packet is None:
                return

            self.log_info(f"Looking at packet: {raw_packet[:20]}")

            # Validate LoRa APRS packet header and structure
            result = is_valid_lora_aprs_packet(raw_packet, self._satellite_message_re)
            if not result == 4:
                self.log_warning(f"Invalid packet format, dropping {result}")
                continue

            # Add asterik to callsign to indicate digipeating
            final_packet = add_asterisk_packet(raw_packet, self._satellite_replace_re,
                                               SATELLITE_RADIO.SC_CALLSIGN)

            # Transmit using special transmit digi packet function
            if not SATELLITE_RADIO.transmit_digi_packet(final_packet):
                self.log_warning("Digipeater TX failed (RF_STOP or radio unavailable)")
