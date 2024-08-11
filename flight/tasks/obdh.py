# Onboard Data Handling (OBDH) Task

from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH


class Task(TemplateTask):

    name = "OBDH"
    ID = 0x02

    # Class variables
    SD_cleaned = False  # TODO DEBUG
    SD_scanned = False
    SD_stored_volume = 0

    async def main_task(self):

        if SM.current_state == "STARTUP":
            if not self.SD_cleaned:
                DH.delete_all_files()
                self.SD_cleaned = True
            if not self.SD_scanned:
                DH.scan_SD_card()
                self.SD_scanned = True

            # TODO Temporarily start global state switch here
            # TODO should have a verification checklist in cdh and switch from there
            SM.switch_to("NOMINAL")
        elif SM.current_state == "NOMINAL":
            self.SD_stored_volume = DH.compute_total_size_files()

        print(f"[{self.ID}][{self.name}] Data processes: {DH.get_all_data_processes_name()}")
        print(f"[{self.ID}][{self.name}] Stored files: {self.SD_stored_volume} bytes.")
