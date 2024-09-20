# Time distribution and handling task

# from hal.pycubed import hardware
import time

from core import TemplateTask
from core import state_manager as SM
from core.states import STATES
from hal.configuration import SATELLITE


class Task(TemplateTask):
    def __init__(self, id):
        super().__init__(id)
        self.name = "TIMING"

    async def main_task(self):

        if SM.current_state == STATES.STARTUP:
            # r = rtc.RTC()
            SATELLITE.RTC.set_datetime(time.struct_time((2024, 4, 24, 9, 30, 0, 3, 115, -1)))
            # rtc.set_time_source(r)
        elif SM.current_state == STATES.NOMINAL:
            self.log_info(f"Time: {int(time.time())}")
            self.log_info(f"Time since boot: {int(time.time()) - SATELLITE.BOOTTIME}")

            """if int(time.time()) - SATELLITE.BOOTTIME > 20:
                time.sleep(10000000)"""
