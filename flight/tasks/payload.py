# Payload Control Task

from apps.payload.controller import PayloadController as PC
from apps.payload.definitions import ExternalRequest
from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STATES


class Task(TemplateTask):

    current_request = ExternalRequest.NO_ACTION

    def __init__(self, id):
        super().__init__(id)
        self.name = "PAYLOAD"
        self.dp_initialized = False
        self.pins_injected = False

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

        # Data process for runtime external requests from the CDH
        if not DH.data_process_exists("payload/requests"):
            DH.register_data_process(tag_name="payload/requests", data_format="B", persistent=False)

    async def main_task(self):
        if SM.current_state == STATES.STARTUP or SM.current_state == STATES.DETUMBLING:
            # Need to inject the communication interface and the power control interface from the HAL here

            if not self.pins_injected:
                # Get the communication interface
                # Get the power control interface
                self.pins_injected = True

        else:
            self.init_all_data_processes()  # Not running payload in detumbling

            if DH.data_process_exists("payload/requests"):
                candidate_request = DH.get_latest_data("payload/requests")[0]
                if candidate_request != ExternalRequest.NO_ACTION:
                    PC.add_request(candidate_request)

            # DO NOT EXPOSE THE LOGIC IN THE TASK
            PC.run_control_logic()
