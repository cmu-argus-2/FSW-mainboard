"""
comms_rev1.py
================
Comms FSW Task
"""

# Argus-1 Radio Libs
from apps.comms.rf_mcu_rev1 import SATELLITE_RADIO

# Template task from taskio
# State manager and OBDH
from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH

# PyCubed Board Lib
from hal.configuration import SATELLITE


class Task(TemplateTask):
    SAT_RADIO = SATELLITE_RADIO(SATELLITE)
    tx_header = 0
    flag_ground_station_pass = True

    async def main_task(self):
        # Only transmit if SAT in NOMINAL state
        if SM.current_state == "NOMINAL":
            # In NOMINAL state, can transmit
            self.flag_ground_station_pass = True

            """
            Heartbeats transmitted every 20s based on task frequency
            Once transmitted, run receive_message, waits for 1s
            """

            # Transmit message
            self.tx_header = self.SAT_RADIO.transmit_message()

            # Debug message
            self.log_info(
                f"Sent message with ID: {self.tx_id}"
            )

            # Receive message, blocking for 1s
            self.flag_ground_station_pass = self.SAT_RADIO.receive_message()