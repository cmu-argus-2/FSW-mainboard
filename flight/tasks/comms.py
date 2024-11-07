# Communication task which uses the radio to transmit and receive messages.
from apps.comms.comms import COMMS_STATE, SATELLITE_RADIO
from apps.telemetry import TelemetryPacker
from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STATES


class Task(TemplateTask):
    tx_msg_id = 0x00
    rq_msg_id = 0x00

    # Setup for heartbeat frequency
    frequency_set = False
    TX_heartbeat_frequency = 0.2  # 5 seconds

    def __init__(self, id):
        super().__init__(id)
        self.name = "COMMS"
        self.comms_state = COMMS_STATE.TX_HEARTBEAT

        # Counters for heartbeat frequency
        self.TX_COUNT_THRESHOLD = 0
        self.TX_COUNTER = 0

        # Counter for ground pass timeout
        self.ground_pass = False
        self.RX_COUNTER = 0

        # TODO: See if needed and remove
        SATELLITE_RADIO.listen()  # RX mode

    async def main_task(self):
        # TODO: Check if this can be done in setup
        if not self.frequency_set:
            # Reset counter
            self.TX_COUNTER = 0

            # Ensure HB frequency not too high
            if self.TX_heartbeat_frequency > self.frequency:
                self.log_error("TX heartbeat frequency faster than task frequency. Defaulting to task frequency.")
                self.TX_heartbeat_frequency = self.frequency

            self.TX_COUNT_THRESHOLD = int(self.frequency / self.TX_heartbeat_frequency)
            self.TX_COUNTER = self.TX_COUNT_THRESHOLD - 1
            self.frequency_set = True

            self.log_info(f"Heartbeat frequency threshold set to {self.TX_COUNT_THRESHOLD}")

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

            # Print current comms state
            self.comms_state = SATELLITE_RADIO.get_state()
            self.log_info(f"Comms state is {self.comms_state}")

            if self.comms_state != COMMS_STATE.RX:
                # Current state is TX state, transmit message

                if self.TX_COUNTER >= self.TX_COUNT_THRESHOLD or self.ground_pass:
                    # Set current TM frame
                    if TelemetryPacker.TM_AVAILABLE and self.comms_state == COMMS_STATE.TX_HEARTBEAT:
                        SATELLITE_RADIO.set_tm_frame(TelemetryPacker.FRAME())

                    # Transmit a message from the satellite
                    self.tx_msg_id = SATELLITE_RADIO.transmit_message()
                    self.TX_COUNTER = 0
                    self.RX_COUNTER = 0

                    # State transition to RX state
                    SATELLITE_RADIO.transition_state(False)

                    self.log_info(f"Sent message with ID: {self.tx_msg_id}")

            else:
                # Current state is RX, receive message

                if SATELLITE_RADIO.data_available():
                    # Read packet present in the RX buffer
                    self.rq_msg_id = SATELLITE_RADIO.receive_message()
                    SATELLITE_RADIO.transition_state(False)

                    # Check the response from the GS
                    if self.rq_msg_id != 0x00:
                        # GS requested valid message ID
                        self.log_info(f"GS requested message ID: {self.rq_msg_id}")
                        self.ground_pass = True
                        self.RX_COUNTER = 0

                    else:
                        # GS requested invalid message ID
                        self.log_warning(f"GS requested invalid message ID: {self.rq_msg_id}")

                else:
                    # No packet received from GS yet
                    self.RX_COUNTER += 1
                    self.log_info(f"Nothing in RX buffer, {self.RX_COUNTER}")

                    if self.RX_COUNTER >= self.TX_COUNT_THRESHOLD:
                        # GS response timeout
                        self.ground_pass = False
                        SATELLITE_RADIO.transition_state(True)
