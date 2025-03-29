# Communication task which uses the radio to transmit and receive messages.
from apps.command import QUEUE_STATUS, CommandQueue, ResponseQueue
from apps.comms.comms import COMMS_STATE, MSG_ID, SATELLITE_RADIO
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
        self.filepath_flag = False

        # IDs returned from application
        self.tx_msg_id = 0x00
        self.rq_cmd = 0x00

        self.rx_payload = bytearray()

        # Setup for heartbeat frequency
        self.frequency_set = False

        self.TX_heartbeat_frequency = 0.2
        self.RX_timeout_frequency = 0.1

        # Counter for TX frequency
        self.TX_COUNT_THRESHOLD = 0
        self.TX_COUNTER = 0

        # Counter for RX frequency
        self.RX_COUNT_THRESHOLD = 0
        self.RX_COUNTER = 0

        # Counter for response timeout
        self.RP_COUNT_THRESHOLD = 0
        self.RP_COUNTER = 0

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

        # Set TX frequency counter and threshold
        self.TX_COUNT_THRESHOLD = int(self.frequency / self.TX_heartbeat_frequency)
        self.TX_COUNTER = self.TX_COUNT_THRESHOLD - 1

        # Ensure RX frequency not too high
        if self.RX_timeout_frequency > self.frequency:
            self.log_error("RX timeout frequency faster than task frequency. Defaulting to task frequency.")
            self.RX_timeout_frequency = self.frequency

        # Set RX frequency counter and threshold
        self.RX_COUNT_THRESHOLD = int(self.frequency / self.RX_timeout_frequency)
        self.RX_COUNTER = 0

        # Set RP frequency counter and threshold
        self.RP_COUNT_THRESHOLD = self.RX_COUNT_THRESHOLD
        self.RP_COUNTER = 0

        # Set flag indicating all counters set
        self.frequency_set = True

        self.log_info(f"Heartbeat frequency threshold set to {self.TX_COUNT_THRESHOLD}")
        self.log_info(f"RX timeout threshold set to {self.RX_COUNT_THRESHOLD}")

    def cls_transmit_message(self):
        if self.TX_COUNTER >= self.TX_COUNT_THRESHOLD or self.ground_pass:
            # If heartbeat TX counter has elapsed, or currently in an active ground pass

            # Set frame / filepath here based on the active GS command
            if not (self.comms_state == COMMS_STATE.TX_HEARTBEAT or self.comms_state == COMMS_STATE.TX_FILEPKT):
                if ResponseQueue.response_available():
                    # The response to the current GS command is ready, downlink it
                    (response_id, response_args), queue_error_code = ResponseQueue.pop_response()

                    # TODO: Receive response based on comms state
                    if self.comms_state == COMMS_STATE.TX_ACK:
                        # Downlinking an ACK to the GS
                        if queue_error_code == QUEUE_STATUS.OK:
                            self.log_info(f"Response: {response_id}, with args: {response_args}")
                            SATELLITE_RADIO.set_tx_ack(response_id)

                    elif self.comms_state == COMMS_STATE.TX_FRAME:
                        # Downlinking telemetry to the GS
                        if queue_error_code == QUEUE_STATUS.OK:
                            self.log_info(f"Response: {response_id}, with args: {response_args}")

                            # Assume we have telemetry packed
                            if TelemetryPacker.TM_AVAILABLE:
                                SATELLITE_RADIO.set_tm_frame(TelemetryPacker.FRAME())

                    elif self.comms_state == COMMS_STATE.TX_METADATA:
                        # Starting a file transfer to the GS
                        if queue_error_code == QUEUE_STATUS.OK:
                            self.log_info(f"Response: {response_id}, with args: {response_args}")

                            # Filepath present in response_args
                            SATELLITE_RADIO.set_filepath(response_args[1])

                    else:
                        # What state is this
                        self.log_error(f"Unknown comms state {self.comms_state}")

                else:
                    # The response to the current GS command not ready, return
                    self.RP_COUNTER += 1

                    if self.RP_COUNTER >= self.RP_COUNT_THRESHOLD:
                        # Timeout in response from commanding
                        # Transition state to RX and hope for the best (RX count values not checked)
                        SATELLITE_RADIO.transition_state(0, 0)
                        self.comms_state = SATELLITE_RADIO.get_state()
                        self.log_error("Commanding response timed out, transitioning to RX")

                    return

            else:
                # Heartbeat or file packet TX, do nothing
                pass

            # Pack telemetry
            if not self.ground_pass:
                self.packed = TelemetryPacker.pack_tm_heartbeat()
                if self.packed:
                    self.log_info("Telemetry heartbeat packed")

            # Set current TM frame
            if TelemetryPacker.TM_AVAILABLE:
                SATELLITE_RADIO.set_tm_frame(TelemetryPacker.FRAME())

            # Transmit a message from the satellite
            self.tx_msg_id = SATELLITE_RADIO.transmit_message()
            self.TX_COUNTER = 0
            self.RX_COUNTER = 0

            # State transition to RX state, values for RX counter not checked
            SATELLITE_RADIO.transition_state(0, 0)
            self.comms_state = SATELLITE_RADIO.get_state()

            self.log_info(f"Sent message with ID: {self.tx_msg_id}")

        else:
            # If not, do nothing
            return

    def cls_receive_message(self):
        if SATELLITE_RADIO.data_available():
            # Read packet present in the RX buffer
            self.rq_cmd = SATELLITE_RADIO.receive_message()

            # Check the response from the GS
            if self.rq_cmd != 0x00:
                # GS requested valid message ID
                self.log_info(f"RX message RSSI: {SATELLITE_RADIO.get_rssi()}")
                self.log_info(f"GS requested command: {self.rq_cmd}")

                # Get most recent payload
                self.rx_payload = SATELLITE_RADIO.get_rx_payload()

                if self.rq_cmd != MSG_ID.GS_CMD_FILE_PKT:
                    # Push rq_cmd onto CommandQueue along with all its arguments
                    CommandQueue.overwrite_command(self.rq_cmd, self.rx_payload)

                # Log RSSI
                DH.log_data("comms", [SATELLITE_RADIO.get_rssi()])

                # Set ground pass true, reset timeout counter
                self.ground_pass = True
                self.RX_COUNTER = 0

            else:
                # GS requested invalid message ID
                self.log_warning(f"GS requested invalid command: {self.rq_cmd}")

        else:
            # Increment RX counter
            self.RX_COUNTER += 1

            # Force RX message ID to be 0x00 for state machine
            SATELLITE_RADIO.set_rx_gs_cmd(0x00)

        # State transition based on RX'd packet
        SATELLITE_RADIO.transition_state(self.RX_COUNTER, self.RX_COUNT_THRESHOLD)
        self.comms_state = SATELLITE_RADIO.get_state()

        if self.comms_state == COMMS_STATE.TX_HEARTBEAT:
            # GS response timeout
            self.ground_pass = False
            self.log_info("Timeout in GS communication")

        else:
            # No timeout yet
            pass

    async def main_task(self):
        # Main comms task loop

        if SM.current_state == STATES.STARTUP:
            # No comms in STARTUP
            pass

        else:
            # Check if TX and RX frequencies are set
            if not self.frequency_set:
                self.cls_change_counter_frequency()

            # Register comms process for logging RX RSSI
            if not DH.data_process_exists("comms"):
                DH.register_data_process("comms", "f", True, 100000)

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
