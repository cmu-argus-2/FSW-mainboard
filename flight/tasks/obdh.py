# Onboard Data Handling (OBDH) Task

import gc

from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STATES


class Task(TemplateTask):
    async def main_task(self):

        if SM.current_state == STATES.STARTUP:
            if not DH.SD_scanned:
                DH.scan_SD_card()
                # DH.update_SD_usage()
                gc.collect()

        elif SM.current_state == STATES.NOMINAL:
            # DH.update_SD_usage()
            pass

        gc.collect()
        self.log_info(f"Data processes: {DH.get_all_data_processes_name()}")
        # self.log_info(f"Stored files: {DH.SD_usage()} bytes.")
