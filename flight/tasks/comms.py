# Communication task which uses the radio to transmit and receive messages.

from apps.comms.rf_mcu import SATELLITE_RADIO
from apps.telemetry import TelemetryPacker
from core import TemplateTask
from core import state_manager as SM
from core.states import STATES


class Task(TemplateTask):
    tx_msg_id = 0x00
    rq_msg_id = 0x00
    msg_cnt = 0
    ground_pass = True

    def __init__(self, id):
        super().__init__(id)
        self.name = "COMMS"
        self.TX_FREQUENCY = 5
        self.TX_COUNTER = 0

        SATELLITE_RADIO.sat.RADIO.listen()

    async def main_task(self):

        if SM.current_state == STATES.NOMINAL:

            """if TelemetryPacker.TM_AVAILABLE:
                SATELLITE_RADIO.tm_frame = TelemetryPacker.FRAME()
            print("RX DONEEE from tasks :::: ", SATELLITE_RADIO.sat.RADIO.rx_done())
            if not self.transmitted:
                # Transmit telemetry at the task rate
                self.tx_msg_id = SATELLITE_RADIO.transmit_message()
                self.log_info(f"Sent message with ID: {self.tx_msg_id}")
                self.transmitted = True

            # If data is in the buffer
            if self.transmitted and SATELLITE_RADIO.sat.RADIO.data_available():
                self.rq_msg_id = SATELLITE_RADIO.receive_message()
                if self.rq_msg_id != 0x00:
                    self.log_info(f"GS requested message ID: {self.rq_msg_id}")
                    self.ground_pass = True
                else:
                    self.log_info("No response from GS")
                    self.ground_pass = False
                    self.msg_cnt = 0

                self.transmitted = False

            if self.ground_pass:
                pass"""

            """while self.msg_cnt < 8 and self.ground_pass is True:
                if TelemetryPacker.TM_AVAILABLE:
                    SATELLITE_RADIO.tm_frame = TelemetryPacker.FRAME()

                    # Transmit telemetry
                    self.tx_msg_id = SATELLITE_RADIO.transmit_message()
                    self.log_info(f"Sent message with ID: {self.tx_msg_id}")

                    self.rq_msg_id = SATELLITE_RADIO.receive_message()

                    if self.rq_msg_id != 0x00:
                        self.log_info(f"GS requested message ID: {self.rq_msg_id}")
                        self.msg_cnt += 1
                        self.ground_pass = True
                    else:
                        self.log_info("No response from GS")
                        self.ground_pass = False
                        self.msg_cnt = 0

            # Reset variables
            self.msg_cnt = 0
            self.ground_pass = True"""

            self.TX_COUNTER += 1

            if self.TX_COUNTER >= self.TX_FREQUENCY:

                if TelemetryPacker.TM_AVAILABLE:
                    SATELLITE_RADIO.tm_frame = TelemetryPacker.FRAME()

                self.tx_msg_id = SATELLITE_RADIO.transmit_message()
                self.log_info(f"Sent message with ID: {self.tx_msg_id}")
                self.TX_COUNTER = 0

                SATELLITE_RADIO.sat.RADIO.listen()

            self.log_info(f"data here?: {SATELLITE_RADIO.sat.RADIO.data_available()}")
            if SATELLITE_RADIO.sat.RADIO.data_available():
                self.rq_msg_id = SATELLITE_RADIO.receive_message()
                # print("task rq_msg_id: ", self.rq_msg_id)
                if self.rq_msg_id != 0x00:
                    self.log_info(f"GS requested message ID: {self.rq_msg_id}")
                else:
                    self.log_info("No response from GS")
