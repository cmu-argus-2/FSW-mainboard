# Payload Control Task

import struct
from io import BytesIO

from apps.payload.controller import PayloadController as PC
from apps.payload.controller import PayloadState, map_state
from apps.payload.definitions import ExternalRequest
from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STATES

_NUM_IMG_TO_MAINTAIN_READY = 1  # Number of images to maintain in memory at least

class Task(TemplateTask):

    current_request = ExternalRequest.NO_ACTION

    def __init__(self, id):
        super().__init__(id)
        self.name = "PAYLOAD"

    def init_all_data_processes(self):
        # Image file process (uses FileProcess for binary file storage)
        if not DH.file_process_exists("img"):
            DH.register_file_process(
                tag_name="img",
                file_extension="bin",
                data_limit=5000000,  # 5MB max per image file
                circular_buffer_size=10,  # Keep 10 images (~530KB), was 20
                buffer_size=8192,  # 8KB write buffer to reduce SD flush frequency during larger bursts
            )

        # Telemetry process
        if not DH.data_process_exists("payload_tm"):
            DH.register_data_process(
                tag_name="payload_tm",
                data_format=PC.tm_process_data_format,
                persistent=True,
                data_limit=100000,
                circular_buffer_size=200,
            )

        # OD process (should be a separate file process)
        if not DH.data_process_exists("payload_od"):
            DH.register_data_process(
                tag_name="payload_od",
                data_format="B" * 10,  # TODO: define proper format
                persistent=True,
                data_limit=1000,
                circular_buffer_size=100,
            )

        # Data process for runtime external requests from the CDH
        if not DH.data_process_exists("payload_requests"):
            DH.register_data_process(tag_name="payload_requests", data_format="B", persistent=False)

    async def main_task(self):
        if SM.current_state == STATES.STARTUP:
            return

        # ===== TESTING ONLY: Force payload to READY state =====
        # Comment this block out for real flight operations
        """
        if PC.state == PayloadState.OFF:
            if not PC.interface_injected():
                PC.load_communication_interface()
            self.init_all_data_processes()

            # Initialize the UART connection (this normally happens in POWERING_ON state)
            if not PC.communication_interface.is_connected():
                PC.initialize()  # This calls connect() on the UART interface
                self.log_info("TEST MODE: Initialized UART connection")

            PC._switch_to_state(PayloadState.READY)  # Skip power-on sequence
            self.log_info("TEST MODE: Forced payload to READY state")
        """
        # ===== END TESTING BLOCK =====

        # Check if any external requests were received irrespective of state
        if DH.data_process_exists("payload_requests") and DH.data_available("payload_requests"):
            candidate_request = DH.get_latest_data("payload_requests")[0]
            if candidate_request != ExternalRequest.NO_ACTION:  # TODO: add timeout in-between requests
                PC.add_request(candidate_request)

        # ===== TESTING ONLY: Skip state machine, only handle READY state =====
        # Comment out this block and uncomment the full state machine below for real flight
        """
        if PC.state == PayloadState.READY:
            if DH.file_process_exists("img"):
                # Check how many complete image files we have
                complete_image_count = DH.get_file_count("img")

                if complete_image_count < _NUM_IMG_TO_MAINTAIN_READY and not PC.file_transfer_in_progress():
                    self.log_info(
                        f"Not enough images in memory ({complete_image_count}/{_NUM_IMG_TO_MAINTAIN_READY}), requesting new image"  # noqa: E501
                    )
                    PC.add_request(ExternalRequest.REQUEST_IMAGE)

        # Run the control logic (handles pings, image transfers, etc.)
        PC.run_control_logic()
        self.log_info(f"Payload state: {map_state(PC.state)}")
        """
        # ===== END TESTING BLOCK =====

        # ===== FULL STATE MACHINE (commented out for testing) =====
        # Uncomment this entire section for real flight operations
        # Replace the testing block above with this

        if SM.current_state != STATES.EXPERIMENT:

            if not PC.interface_injected():
                PC.load_communication_interface()

            # Need to handle issues with power control eventually or log error codes for the HAL

            self.init_all_data_processes()

            # Two cases:
            #  - Satellite has booted up and we need to initialize the payload
            #  - State transitioned out of EXPERIMENT and we need to stop the payload gracefully
            #    (forcefully in worst-case scenarios)

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

            elif PC.state == PayloadState.READY:
                if DH.file_process_exists("img"):
                    # Check how many complete image files we have
                    complete_image_count = DH.get_file_count("img")

                    if (
                        complete_image_count < _NUM_IMG_TO_MAINTAIN_READY
                        and not PC.file_transfer_in_progress()
                    ):
                        self.log_info(
                            f"Not enough images in memory "
                            f"({complete_image_count}/{_NUM_IMG_TO_MAINTAIN_READY}), requesting new image"
                        )
                        PC.add_request(ExternalRequest.REQUEST_IMAGE)

        # DO NOT EXPOSE THE LOGIC IN THE TASK and KEEP EVERYTHING INTERNAL
        PC.run_control_logic()
        self.log_info(f"Payload state: {map_state(PC.state)}")
        
        # ===== END FULL STATE MACHINE =====
