# Payload Control Task

from apps.payload.controller import PayloadController as PC
from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STATES


class Task(TemplateTask):

    # TODO: request queue

    def __init__(self, id):
        super().__init__(id)
        self.name = "PAYLOAD"

    async def main_task(self):
        if SM.current_state == STATES.STARTUP:
            # Grab the communication interface from SATELLITE
            pass
        else:
            if not DH.data_process_exists("img"):
                DH.register_image_process()  # WARNING: Image process from DH is different from regular data processes!

            # TODO: other commands and logging here
