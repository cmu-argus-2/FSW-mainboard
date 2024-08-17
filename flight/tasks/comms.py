# Communication task which uses the radio to transmit and receive messages.

from apps.comms.rf_mcu import RF_MCU
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

                # Transmit telemetry
                self.tx_id = RF_MCU.transmit(TelemetryPacker.FRAME())
                self.log_info(
                    f"Sent message with ID: {self.tx_id} \
                    - SEQ_COUNT: {TelemetryPacker.SEQ_COUNT()} \
                    - PACKET LENGTH: {TelemetryPacker.PACKET_LENGTH()} bytes"
                )
