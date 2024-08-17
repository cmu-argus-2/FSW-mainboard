# Time distribution and handling task

import time

from flight.core import TemplateTask
from flight.core import state_manager as SM


class Task(TemplateTask):

    name = "TIMING"
    ID = 0x01

    async def main_task(self):

        print(f"[{self.ID}][{self.name}] GLOBAL STATE: {SM.current_state}.")
        print(f"[{self.ID}][{self.name}] Time: {int(time.time())}")

        if SM.current_state == "STARTUP":
            SM.switch_to("NOMINAL")
