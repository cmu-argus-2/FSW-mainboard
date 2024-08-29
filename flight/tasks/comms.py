# Communication task which uses the radio to transmit and receive messages.

from apps.comms.rf_mcu_rev1 import SATELLITE_RADIO
from apps.telemetry import TelemetryPacker
from core import TemplateTask
from core import state_manager as SM
from core.states import STATES


class Task(TemplateTask):
    tx_header = 0

    async def main_task(self):

        if SM.current_state == STATES.NOMINAL:

            # Pack telemetry at the task rate

            if TelemetryPacker.TM_AVAILABLE:
                SATELLITE_RADIO.tm_frame = bytearray([0x01, 0x00, 0x01, 0x04, 0xFF, 0xEE, 0xDD, 0xCC])

                # Transmit telemetry
                self.tx_id = SATELLITE_RADIO.transmit_message()
                self.log_info(
                    f"Sent message with ID: {self.tx_id} - SEQ_COUNT: {SATELLITE_RADIO.tm_frame[1:3]} - PACKET LENGTH: {SATELLITE_RADIO.tm_frame[3]} bytes"
                )
