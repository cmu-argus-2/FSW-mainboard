# Communication task which uses the radio to transmit and receive messages.

from apps.comms import SATELLITE_RADIO
from apps.telemetry import TelemetryPacker
from core import TemplateTask
from core import state_manager as SM
from core.states import STATES
from core.data_handler import DataHandler as DH

class Task(TemplateTask):
    tx_msg_id = 0x00
    rq_msg_id = 0x00

    # Setup for heartbeat frequency
    frequency_set = False
    TX_heartbeat_frequency = 0.2  # 5 seconds

    def __init__(self, id):
        super().__init__(id)
        self.name = "COMMS"

        # Counters for heartbeat frequency
        self.TX_COUNT_THRESHOLD = 0
        self.TX_COUNTER = 0

        SATELLITE_RADIO.listen()  # RX mode

    async def main_task(self):

        if not self.frequency_set:
            # Reset counter and ensure HB frequency not too high
            self.TX_COUNTER = 0

            if self.TX_heartbeat_frequency > self.frequency:
                self.log_error("TX heartbeat frequency faster than task frequency")

            # Set frequency
            self.TX_COUNT_THRESHOLD = int(self.frequency / self.TX_heartbeat_frequency)
            self.frequency_set = True

        if SM.current_state == STATES.NOMINAL:
            if not DH.data_process_exists("img"):
                # TODO: Move image process to another task
                DH.register_data_process("img", "b", True)

                # Set filepath for comms TX file
                filepath = DH.request_TM_path_image()
                SATELLITE_RADIO.set_filepath(filepath)
                self.log_info(f"Initializing TX file filepath: {filepath}")

            # Increment counter
            self.TX_COUNTER += 1

            # TODO: Add check for comms FSW state in this
            if self.TX_COUNTER >= self.TX_COUNT_THRESHOLD:
                # Send out message
                if TelemetryPacker.TM_AVAILABLE:
                    SATELLITE_RADIO.set_tm_frame(TelemetryPacker.FRAME())

                self.tx_msg_id = SATELLITE_RADIO.transmit_message()
                self.log_info(f"Sent message with ID: {self.tx_msg_id}")
                self.TX_COUNTER = 0

                SATELLITE_RADIO.listen()  # RX mode

            if SATELLITE_RADIO.data_available():
                # Read packet present in the RX buffer
                self.rq_msg_id = SATELLITE_RADIO.receive_message()
                if self.rq_msg_id != 0x00:
                    self.log_info(f"GS requested message ID: {self.rq_msg_id}")
            else:
                # No packet received from GS yet
                self.log_info("Nothing in RX buffer")