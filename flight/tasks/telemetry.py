# Telemetry packing for transmission

from apps.telemetry import TelemetryPacker
from core import TemplateTask
from core import state_manager as SM
from core.states import STATES


class Task(TemplateTask):

    packed = False

    def __init__(self, id):
        super().__init__(id)
        self.name = "TM"

    async def main_task(self):

        if SM.current_state == STATES.STARTUP:
            pass

        elif SM.current_state == STATES.NOMINAL:

            # Pack telemetry at the task rate
            self.packed = TelemetryPacker.pack_tm_frame()
            if self.packed:
                self.log_info("Telemetry packed")
