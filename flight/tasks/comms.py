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
                SATELLITE_RADIO.tm_frame = TelemetryPacker.FRAME()

                # Transmit telemetry
                self.tx_id = SATELLITE_RADIO.transmit_message()
                self.log_info(
                    f"Sent message with ID: {self.tx_id}, Length: {len(SATELLITE_RADIO.tm_frame)}"
                )
