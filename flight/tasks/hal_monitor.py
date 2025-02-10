# Hardware watchdog and HAL monitor task
# This task is responsible for monitoring the health of the hardware abstraction layer (HAL),
# performing diagnostics in case of failure, and reporting/logging HAL status.

from core import TemplateTask
from core import state_manager as SM
from core.states import STATES
from hal.configuration import SATELLITE


class Task(TemplateTask):
    def __init__(self, id):
        super().__init__(id)
        self.name = "HAL_MONITOR"

    async def main_task(self):
        # TODO: toggle HW watchdog pin (do it first, irrespective of state logic)

        if SM.current_state == STATES.STARTUP:
            # TODO: Enable HW watchdog (note that the pin must be toggled beforehand)
            
            pass
        else:
            pass
