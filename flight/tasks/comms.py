# Communication task which uses the radio to transmit and receive messages.

from apps.comms.rf_mcu import SATELLITE_RADIO
from apps.telemetry import TelemetryPacker
from core import TemplateTask
from core import state_manager as SM
from core.states import STATES


class Task(TemplateTask):
    tx_msg_id = 0x00
    rq_msg_id = 0x00

    async def main_task(self):

        if SM.current_state == STATES.NOMINAL:

            # Pack telemetry at the task rate

            if TelemetryPacker.TM_AVAILABLE:
                SATELLITE_RADIO.tm_frame = TelemetryPacker.FRAME()

                # Transmit telemetry
                self.tx_msg_id = SATELLITE_RADIO.transmit_message()
                self.log_info(f"Sent message with ID: {self.tx_msg_id}")

                self.rq_msg_id = SATELLITE_RADIO.receive_message()

                if self.rq_msg_id != 0x00:
                    self.log_info(f"GS requested message ID: {self.rq_msg_id}")
                else:
                    self.log_info("No response from GS")
