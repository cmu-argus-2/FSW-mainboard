# Communication task which uses the radio to transmit and receive messages.
from apps.comms.comms import COMMS_STATE, SATELLITE_RADIO
from apps.telemetry import TelemetryPacker
from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STATES


class Task(TemplateTask):
    def __init__(self, id):
        super().__init__(id)

        self.name = "COMMS"
        self.comms_state = COMMS_STATE.TX_HEARTBEAT

        # IDs returned from application
        self.tx_msg_id = 0x00
        self.rq_msg_id = 0x00

        # Setup for heartbeat frequency
        self.frequency_set = False

        self.TX_heartbeat_frequency = 0.5
        self.RX_timeout_frequency = 0.5

        # Counter for TX frequency
        self.TX_COUNT_THRESHOLD = 0
        self.TX_COUNTER = 0

        # Counter for RX frequency
        self.RX_COUNT_THRESHOLD = 0
        self.RX_COUNTER = 0

        # Counter for ground pass timeout
        self.ground_pass = False

    def cls_change_counter_frequency(self):
        # Reset counter
        self.TX_COUNTER = 0
        self.RX_COUNTER = 0

        # Ensure TX frequency not too high
        if self.TX_heartbeat_frequency > self.frequency:
            self.log_error("TX heartbeat frequency faster than task frequency. Defaulting to task frequency.")
            self.TX_heartbeat_frequency = self.frequency

        self.TX_COUNT_THRESHOLD = int(self.frequency / self.TX_heartbeat_frequency)
        self.TX_COUNTER = self.TX_COUNT_THRESHOLD - 1

        # Ensure RX frequency not too high
        if self.RX_timeout_frequency > self.frequency:
            self.log_error("RX timeout frequency faster than task frequency. Defaulting to task frequency.")
            self.RX_timeout_frequency = self.frequency

        self.RX_COUNT_THRESHOLD = int(self.frequency / self.RX_timeout_frequency)
        self.RX_COUNTER = 0

        self.frequency_set = True

        self.log_info(f"Heartbeat frequency threshold set to {self.TX_COUNT_THRESHOLD}")
        self.log_info(f"RX timeout threshold set to {self.RX_COUNT_THRESHOLD}")

    def cls_transmit_message(self):
        if self.TX_COUNTER >= self.TX_COUNT_THRESHOLD or self.ground_pass:
            # If heartbeat TX counter has elapsed, or currently in an active ground pass

            # TODO: Set frame / filepath here based on the active GS command

            # Pack telemetry
            self.packed = TelemetryPacker.pack_tm_frame()
            if self.packed:
                self.log_info("Telemetry packed")

            # Set current TM frame
            if TelemetryPacker.TM_AVAILABLE and self.comms_state == COMMS_STATE.TX_HEARTBEAT:
                SATELLITE_RADIO.set_tm_frame(TelemetryPacker.FRAME())

            # Transmit a message from the satellite
            self.tx_msg_id = SATELLITE_RADIO.transmit_message()
            self.TX_COUNTER = 0
            self.RX_COUNTER = 0

            # State transition to RX state
            SATELLITE_RADIO.transition_state(False)
            self.comms_state = SATELLITE_RADIO.get_state()

            self.log_info(f"Sent message with ID: {self.tx_msg_id}")
        else:
            # If not, do nothing
            pass

    def cls_receive_message(self):
        if SATELLITE_RADIO.data_available():
            # Read packet present in the RX buffer
            self.rq_msg_id = SATELLITE_RADIO.receive_message()

            # State transition based on RX'd packet
            SATELLITE_RADIO.transition_state(False)
            self.comms_state = SATELLITE_RADIO.get_state()

            # Check the response from the GS
            if self.rq_msg_id != 0x00:
                # GS requested valid message ID
                self.log_info(f"RX message RSSI: {SATELLITE_RADIO.get_rssi()}")
                self.log_info(f"GS requested message ID: {self.rq_msg_id}")

                DH.log_data("comms", [SATELLITE_RADIO.get_rssi()])

                self.ground_pass = True
                self.RX_COUNTER = 0

            else:
                # GS requested invalid message ID
                self.log_warning(f"GS requested invalid message ID: {self.rq_msg_id}")

        else:
            # No packet received from GS yet
            self.RX_COUNTER += 1

            if self.RX_COUNTER >= self.RX_COUNT_THRESHOLD:
                # GS response timeout
                self.ground_pass = False

                # State transition back to TX_HEARTBEAT state
                SATELLITE_RADIO.transition_state(True)
                self.comms_state = SATELLITE_RADIO.get_state()

                self.log_info("Timeout in GS communication")
            else:
                # No timeout yet
                pass

    async def main_task(self):
        # Main comms task loop
        if not DH.data_process_exists("comms"):
            DH.register_data_process("comms", "f", True, 100000)

        if not self.frequency_set:
            self.cls_change_counter_frequency()

        if SM.current_state == STATES.NOMINAL or SM.current_state == STATES.DOWNLINK:
            if not DH.data_process_exists("img"):
                # TODO: Move image process to another task
                DH.register_data_process("img", "b", True)

                # Set filepath for comms TX file
                filepath = DH.request_TM_path_image()
                SATELLITE_RADIO.set_filepath(filepath)
                self.log_info(f"Initializing TX file filepath: {filepath}")

            # Increment counter
            self.TX_COUNTER += 1

            # Get current comms state
            self.comms_state = SATELLITE_RADIO.get_state()
            
            if self.comms_state != COMMS_STATE.RX:
                # Current state is TX state, transmit message
                self.cls_transmit_message()
            else:
                # Current state is RX, receive message
                self.cls_receive_message()
