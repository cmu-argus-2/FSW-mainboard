# Telemetry packing for transmission

from core import TemplateTask
from core import state_manager as SM
from core.states import STATES


class Task(TemplateTask):

    name = "TM"
    ID = 0x12

    async def main_task(self):

        if SM.current_state == STATES.STARTUP:
            pass

        elif SM.current_state == STATES.NOMINAL:
            pass

        print(f"[{self.ID}][{self.name}] ...")
