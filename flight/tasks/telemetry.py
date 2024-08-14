# Telemetry packing for transmission

from apps.telemetry import TelemetryPacker
from core import TemplateTask
from core import state_manager as SM
from core.states import STATES


class Task(TemplateTask):

    name = "TM"
    ID = 0x12

    packed = False

    async def main_task(self):

        if SM.current_state == STATES.STARTUP:
            pass

        elif SM.current_state == STATES.NOMINAL:

            self.packed = TelemetryPacker.pack_tm_frame()
            if self.packed:
                self.log_info("Telemetry packed")
                self.log_info(TelemetryPacker.PACKET)
