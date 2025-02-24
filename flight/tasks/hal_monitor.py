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

        if SM.current_state == STATES.STARTUP:
            for name, device in SATELLITE.ERRORS.items():
                if device[0] == 1:
                    SM.set_state(STATES.HAL_ERROR)
                    SM.set_error(name, device[1])
                else:
                    pass
        else:
            pass
