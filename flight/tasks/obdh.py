# Onboard Data Handling (OBDH) Task

from core import DataHandler as DH
from core import TemplateTask
from core import state_manager as SM
from core.states import STATES


class Task(TemplateTask):

    frequency_set = False
    cleanup_frequency = 0.1  # 10 seconds

    def __init__(self, id):
        super().__init__(id)
        self.name = "OBDH"
        self.CLEANUP_COUNT_THRESHOLD = 0
        self.CLEANUP_COUNTER = 0

    async def main_task(self):

        if SM.current_state == STATES.STARTUP:
            if not DH.SD_SCANNED():
                DH.scan_SD_card()
                # DH.update_SD_usage()

        else:  # Run for all other states

            if not self.frequency_set:
                self.CLEANUP_COUNTER = 0
                if self.cleanup_frequency > self.frequency:
                    self.log_error("Clean-up frequency faster than task frequency. Defaulting to task frequency.")
                    self.cleanup_frequency = self.frequency
                self.CLEANUP_COUNT_THRESHOLD = int(self.frequency / self.cleanup_frequency)
                self.frequency_set = True

            self.CLEANUP_COUNTER += 1

            if self.CLEANUP_COUNTER >= self.CLEANUP_COUNT_THRESHOLD:
                DH.check_circular_buffers()
                DH.clean_up()  # Clean up path that have been marked for deletion
                self.CLEANUP_COUNTER = 0

            if SM.current_state == STATES.NOMINAL:
                pass

            self.log_info(f"Data processes: {DH.get_all_data_processes_name()}")
            # self.log_info(f"Stored files: {DH.SD_usage()} bytes.")
