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

    def init_all_data_processes(self):
        # Image process
        if not DH.data_process_exists("payload/img"):
            DH.register_image_process()  # WARNING: Image process from DH is different from regular data processes!

        # Telemetry process
        if not DH.data_process_exists("payload/tm"):
            data_format = 3 * "L" + 4 * "B" + 4 * "B" + 4 * "B" + 8 * "B" + 3 * "H"
            DH.register_data_process(tag_name="payload/tm", data_format=data_format, persistent=True, data_limit=100000)

        # OD process (should be a separate data process)
        if not DH.data_process_exists("payload/od"):
            pass

    async def main_task(self):
        if SM.current_state == STATES.STARTUP:
            # Grab the communication interface from SATELLITE
            pass
        else:
            self.init_all_data_processes()
