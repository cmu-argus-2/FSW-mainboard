# Onboard Data Handling (OBDH) Task

from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STATES


class Task(TemplateTask):

    name = "OBDH"
    ID = 0x02

    async def main_task(self):

        if SM.current_state == STATES.STARTUP:
            if not DH.SD_scanned:
                DH.scan_SD_card()
                DH.update_SD_usage()

        elif SM.current_state == STATES.NOMINAL:
            DH.update_SD_usage()

        print(f"[{self.ID}][{self.name}] Data processes: {DH.get_all_data_processes_name()}")
