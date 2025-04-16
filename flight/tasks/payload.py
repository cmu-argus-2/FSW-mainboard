# Payload Control Task

from apps.payload.controller import PayloadController as PC
from apps.payload.controller import PayloadState
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

    def init_all_data_processes(self):
        # Image process
        if not DH.data_process_exists("img"):
            DH.register_image_process()  # WARNING: Image process from DH is different from regular data processes!

        # Telemetry process
        if not DH.data_process_exists("payload_tm"):
            data_format = 3 * "L" + 4 * "B" + 4 * "B" + 4 * "B" + 8 * "B" + 3 * "H"
            DH.register_data_process(tag_name="payload_tm", data_format=data_format, persistent=True, data_limit=100000)

        # OD process (should be a separate data process)
        if not DH.data_process_exists("payload_od"):
            pass

        # Data process for runtime external requests from the CDH
        if not DH.data_process_exists("payload_requests"):
            DH.register_data_process(tag_name="payload_requests", data_format="B", persistent=False)

    async def main_task(self):

        if SM.current_state == STATES.STARTUP:
            return

        # Check if any external requests were received irrespective of state
        if DH.data_process_exists("payload/requests"):
            candidate_request = DH.get_latest_data("payload/requests")[0]
            if candidate_request != ExternalRequest.NO_ACTION:  # TODO: add timeout in-between requests
                PC.add_request(candidate_request)

        if SM.current_state != STATES.EXPERIMENT:

            if not PC.interface_injected():
                PC.load_communication_interface()

            # Need to handle issues with power control eventually or log error codes for the HAL

            self.init_all_data_processes()

            """
            Two cases:
             - Satellite has booted up and we need to initialize the payload
             - State transitioned out of EXPERIMENT and we need to stop the payload gracefully
               (forcefully in worst-case scenarios)
            """

            # TODO: This is going to change
            if PC.state != PayloadState.OFF:  # All good

                PC.add_request(ExternalRequest.TURN_OFF)

                if PC.state == PayloadState.SHUTTING_DOWN:
                    # TODO: check timeout just in case. However, this will be handled internally.
                    PC.add_request(ExternalRequest.FORCE_POWER_OFF)
                    pass

        else:  # EXPERIMENT state

            if PC.state == PayloadState.OFF:
                PC.add_request(ExternalRequest.TURN_ON)

        # DO NOT EXPOSE THE LOGIC IN THE TASK and KEEP IT INTERNAL
        PC.run_control_logic()
