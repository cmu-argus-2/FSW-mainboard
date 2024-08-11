"""
radio_comms.py
================
Comms FSW Task
"""

# Argus-1 Radio Libs
from apps.comms.radio_helpers import SATELLITE_RADIO

# Template task from taskio
# State manager and OBDH
from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH

# PyCubed Board Lib
from hal.configuration import SATELLITE


class Task(TemplateTask):

    name = "COMMS"
    ID = 0x12

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

            while self.flag_ground_station_pass:
                # Check if an image is available for downlinking
                if DH.data_process_exists("img"):
                    tm_path = DH.request_TM_path_image()
                    if tm_path is not None:
                        # Image available, change filepath
                        print(
                            f"[{self.ID}][{self.name}] Onboard image at:",
                            tm_path,
                        )
                        self.SAT_RADIO.image_strs = [tm_path]
                        self.SAT_RADIO.image_get_info()
                    else:
                        # No image available, use empty filepath
                        print(f"[{self.ID}][{self.name}] No image onboard")
                        self.SAT_RADIO.image_strs = []
                        self.SAT_RADIO.image_get_info()
                else:
                    # No image available, use empty filepath
                    print(f"[{self.ID}][{self.name}] No image process")
                    self.SAT_RADIO.image_strs = []
                    self.SAT_RADIO.image_get_info()

                # Transmit message
                self.tx_header = self.SAT_RADIO.transmit_message()

                # Debug message
                print(
                    f"[{self.ID}][{self.name}] Sent message with ID:",
                    self.tx_header,
                )

                # Receive message, blocking for 1s
                self.flag_ground_station_pass = self.SAT_RADIO.receive_message()

                if self.SAT_RADIO.image_done_transmitting():
                    print(f"[{self.ID}][{self.name}] Image downlinked, deleting with OBDH")
                    DH.notify_TM_path("img", tm_path)
                    DH.clean_up()
