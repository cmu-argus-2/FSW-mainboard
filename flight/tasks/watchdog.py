# Hardware watchdog task
# This task is responsible for toggling the hardware watchdog pin to prevent
# the system from resetting unexpectedly and to ensure that the system is
# functioning correctly.

from core import TemplateTask
from hal.configuration import SATELLITE


class Task(TemplateTask):
    def __init__(self, id):
        super().__init__(id)
        self.name = "WATCHDOG"

    async def main_task(self):
        # if SATELLITE.WATCHDOG_AVAILABLE:
        #     if not SATELLITE.WATCHDOG.enabled:
        #         self.log_info("Watchdog enabled.")
        #         SATELLITE.WATCHDOG.enable()

        #     if SATELLITE.WATCHDOG.input:
        #         SATELLITE.WATCHDOG.input_low()
        #     else:
        #         SATELLITE.WATCHDOG.input_high()
        pass
