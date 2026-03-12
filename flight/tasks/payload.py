# Payload Control Task

from apps.payload.controller import PayloadController as PC
from apps.payload.controller import PayloadState, map_state
from apps.payload.definitions import ExternalRequest
from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STATES

from core.time_processor import TimeProcessor as TPM

from apps.telemetry.splat.splat.telemetry_codec import Command, pack


_NUM_IMG_TO_MAINTAIN_READY = 1  # Number of images to maintain in memory at least


class Task(TemplateTask):

    current_request = ExternalRequest.NO_ACTION
    _last_state_print_ts = 0  # Track last time state was printed

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


        # TODO - not sure what this is for
        # OD process (should be a separate file process)
        if not DH.data_process_exists("payload_od"):
            DH.register_data_process(
                tag_name="payload_od",
                data_format="B" * 10,  # TODO: define proper format
                persistent=True,
                data_limit=1000,
                circular_buffer_size=100,
            )

        # TODO - dont need this anymore as I will have a command list
        # # Data process for runtime external requests from the CDH
        # if not DH.data_process_exists("payload_requests"):
        #     DH.register_data_process(tag_name="payload_requests", data_format="B", persistent=False)

    def run_idle_state(self):
        """
        This is the function that will run when the payload is in idle state
        It will be in idle state while it has no commands to be processed
        It will simply look at the the command list to see if there are any commands
            if there are commands, it will change to watching state
        If there are no commands, it will just return
        """
        self.log_info("Running payload")
        
        if PC.command_available():
            # means that we now have a command that is available, want to switch state to watching
            self.log_info("Command available, switching to watching state.")
            PC.switch_state("WATCHING")
            return
        
        # no command available, nothing to do
        return

    def run_watching_state(self):
        """
        This is the second state in the process
        Used to allow scheduling of comamnds. It will get the first command on the list of commands
            list of commands is ordered by timestamp
        and will check the timestamp of the command to the current timestamp
        
        if command timestmap < current timestamp it will change to booting mode 
        
        TODO - add margin to make sure that we turn the payload a few moments before the actual time
        """
        
        command = PC.get_first_command()
        self.log_info(f"Watching for command: {command}")
        # check to see if the time to execute the command has arrived
        if command[0] < TPM.time() or command[0] == 0:
            # means that it is time to run the command
            self.log_info("Command time has arrived, switching to booting state.")
            PC.BOOT_TS = TPM.time()
            PC.received_ping_ack = False
            PC.switch_state("BOOTING")
            return
        
        self.log_info(f"   Missing {command[0] - TPM.time()} seconds")
    
        # not time to run the command yet
        return

    def run_booting_state(self):
        """
        This state will be responsible for making sure that the jetson boots up
        the jetson will be turned on in the change state function to guarantee that we are only doing it once
        after that, every time this runs it will send a ping command and wait for a response
            once it has received a response it will move state ACTIVE
        it has a timeout where it will go to fail state and turn of the jetson
        """
        
        # check to see if we got response from ping
        if PC.received_ping_ack:
            # means we have received a response from jetson, moving to ACTIVE state
            self.log_info("Ping responded, switching to ACTIVE state.")
            PC.received_experiment_ack = False
            PC.switch_state("ACTIVE")
            return
        
        PC.send_ping()  # if we send before checking received ping we might send twice
        
        # check timeout 
        if PC.BOOT_TS + PC.BOOT_TIMEOUT <= TPM.time():
            self.log_error("Boot timeout reached, switching to FAIL state.")
            PC.switch_state("FAIL")
            return

        # no response from pign and no timeout
        return
    
    def run_active_state(self):
        """
        This state will be responsible for forwarding the command to the jetson
        At this stage the jetson is alive and is waiting for instructions on what to do
        So here we will just send the command
        We will keep on sending the command until ack for the command has been received
            once received, it will move on to processing mode
        command has already been choosen and removed from the list in switch state
        """
        
        # wait for a response
        if PC.received_experiment_ack:
            # means that we have received the response to the command (jetson has received command)
            # TODO - should check if the command is valid
            self.log_info("Command ack received, switching to PROCESSING state.")
            PC.PROC_TS = TPM.time()
            PC.received_experiment_finished = False
            PC.switch_state("PROCESSING")
            return
        
        # send the command
        PC.send_current_command()  # current command was choosen in switch state
            
    def run_processing_state(self):
        """
        This is the state we will be at while waiting for the jetson to run the command
        when in this state the jetson is already on, has received the command
        this state will only periodically ask for a telemetry packet
        it will also check the timeout
        It will check if the message from jetson for processing finished has been received
        """

        if PC.PROC_TS + PC.PROC_TIMEOUT <= TPM.time():
            # means that we have reached the timeout of the command
            self.log_info("Processing timeout reached, switching to FAIL state.")
            PC.switch_state("FAIL")
            return

        if PC.TELEM_TS + PC.TELEM_PERIOD <= TPM.time():
            self.log_info("Sending telemetry request.")
            PC.TELEM_TS = TPM.time()
            PC.send_telemetry_command()

        # check to see if processing is finished
        if PC.received_experiment_finished:
            self.log_info("Processing finished, switching to FINISHED state.")
            PC.switch_state("FINISHED")
            return
        
        

    def run_finished_state(self):
        """
        This state will be reached once jetson has finished processing the command
            it will send a message in uart to let the satellite know
        Not sure what to do with this state, for now we will just skip onto the next state
        """
        # TODO - check if this state is needed
        print("Finished state reached.")
        
        # move directly to download state
        PC.switch_state("DOWNLOAD")
        
        return
    
    def run_download_state(self):
        """
        Download state: delegate file download orchestration to DownloadManager.
        
        This state processes file downloads from the payload in batches:
        1. Receive and process one batch of packets (32 packets default)
        2. Generate confirmation bitmap
        3. Send confirmation to jetson
        4. Check if file is complete
        5. If complete, finalize and move to next file
        6. If no more files, exit to OFF state
        """
        
        # If no transactions to process yet, wait for them
        if not PC.received_create_trans or not PC.received_init_trans:
            return
        
        # Get current download status
        status = PC.get_download_status()

        # Only leave DOWNLOAD when the payload explicitly reports that all files were sent
        if not status['has_active_file']:
            if PC.received_all_files_sent:
                self.log_info("Payload reported all files sent, transitioning to OFF state.")
                PC.switch_state("OFF")
            else:
                self.log_info("No active file right now; waiting for next file or completion signal from payload.")
            return
        
        try:
            # Process one batch: listen, save, generate bitmap
            msb, lsb = PC.download_manager.process_batch(PC.process_uart)

            if msb is None or lsb is None:
                return

            status = PC.get_download_status()
            
            # Send confirmation to jetson
            command = Command("CONFIRM_LAST_BATCH")
            command.add_argument("tid", status['current_tid'])
            command.add_argument("MSB", msb)
            command.add_argument("LSB", lsb)
            PC.send_confirm_last_batch(command)
            
            self.log_info(
                f"Sent CONFIRM_LAST_BATCH: tid={status['current_tid']}, MSB=0x{msb:04X}, LSB=0x{lsb:04X}, missing={status['missing_fragments']}"
            )
            
            # Check if file is complete
            if PC.download_manager.is_file_complete():
                self.log_info(
                    f"File complete for tid={status['current_tid']}, finalizing..."
                )
                
                # Finalize current file (write, verify, cleanup)
                if PC.download_manager.finalize_file():
                    self.log_info(
                        f"File finalized successfully for tid={status['current_tid']}"
                    )
                    
                    # Move to next file in queue
                    if PC.download_manager.advance_to_next_file():
                        self.log_info("Advanced to next file in queue")
                    else:
                        self.log_info("No more files currently queued; waiting for payload to send next file or completion signal")
                else:
                    self.log_error(
                        f"Failed to finalize file for tid={status['current_tid']}"
                    )
                    PC.switch_state("FAIL")
                    return
            else:
                # More batches to process for this file
                PC.download_manager.advance_batch()
        
        except Exception as e:
            self.log_error(f"Error during download processing: {e}")
            PC.switch_state("FAIL")
        

    def run_off_state(self):
        """
        This is the state that will cut the power to the jetson
        A command will be sent to the jetson to turn it off when switching state
        This state will look for the ack of that command
            once received it will cut the power to the jetson
        if timeout reaches it will also cut the power to the jetson
        go back to idle mode
        """
        
        if PC.received_off_ack:
            # we have received response from jetson, safe to turn off
            self.log_info("Turn off ack received, cutting power to jetson.")
        
        if PC.OFF_TS + PC.OFF_TIMEOUT <= TPM.time():
            self.log_info("Turn off timeout reached, cutting power to jetson.")
            PC.turn_off_power()
            PC.switch_state("IDLE")
    
    def run_fail_state(self):
        """
        This is the state we will be in if there is any problem or any timeout
        It will warn that there was an error, cut the power to the jetson and
        go back to idle mode
        """
            
        self.log_error("[PAYLOAD] - Fail state reached, cutting power to jetson.")
        PC.turn_off_power()
        PC.switch_state("IDLE")

    async def main_task(self):
        
        if PC.current_state == 0:
            self.run_idle_state()
        if PC.current_state == 1:
            self.run_watching_state()
        if PC.current_state == 2:
            self.run_booting_state()
        if PC.current_state == 3:
            self.run_active_state()
        if PC.current_state == 4:
            self.run_processing_state()
        if PC.current_state == 5:
            self.run_finished_state()
        if PC.current_state == 6:
            self.run_download_state()
        if PC.current_state == 7:
            self.run_off_state()
        if PC.current_state == 8:
            self.run_fail_state()

        if TPM.time() - self._last_state_print_ts >= 5:
            self._last_state_print_ts = TPM.time()
            print(f"[PAYLOAD] Current state: {PC.current_state}")
            
        PC.process_uart()
            
    # async def main_task(self):
    #     if SM.current_state == STATES.STARTUP:
    #         return

    #     # ===== TESTING ONLY: Force payload to READY state =====
    #     # Comment this block out for real flight operations
    #     """
    #     if PC.state == PayloadState.OFF:
    #         if not PC.interface_injected():
    #             PC.load_communication_interface()
    #         self.init_all_data_processes()

    #         # Initialize the UART connection (this normally happens in POWERING_ON state)
    #         if not PC.communication_interface.is_connected():
    #             PC.initialize()  # This calls connect() on the UART interface
    #             self.log_info("TEST MODE: Initialized UART connection")

    #         PC._switch_to_state(PayloadState.READY)  # Skip power-on sequence
    #         self.log_info("TEST MODE: Forced payload to READY state")
    #     """
    #     # ===== END TESTING BLOCK =====

    #     # Check if any external requests were received irrespective of state
    #     if DH.data_process_exists("payload_requests") and DH.data_available("payload_requests"):
    #         candidate_request = DH.get_latest_data("payload_requests")[0]
    #         if candidate_request != ExternalRequest.NO_ACTION:  # TODO: add timeout in-between requests
    #             PC.add_request(candidate_request)

    #     # ===== TESTING ONLY: Skip state machine, only handle READY state =====
    #     # Comment out this block and uncomment the full state machine below for real flight
    #     """
    #     if PC.state == PayloadState.READY:
    #         if DH.file_process_exists("img"):
    #             # Check how many complete image files we have
    #             complete_image_count = DH.get_file_count("img")

    #             if complete_image_count < _NUM_IMG_TO_MAINTAIN_READY and not PC.file_transfer_in_progress():
    #                 self.log_info(
    #                     f"Not enough images in memory ({complete_image_count}/{_NUM_IMG_TO_MAINTAIN_READY}), requesting new image"  # noqa: E501
    #                 )
    #                 PC.add_request(ExternalRequest.REQUEST_IMAGE)

    #     # Run the control logic (handles pings, image transfers, etc.)
    #     PC.run_control_logic()
    #     self.log_info(f"Payload state: {map_state(PC.state)}")
    #     """
    #     # ===== END TESTING BLOCK =====

    #     # ===== FULL STATE MACHINE (commented out for testing) =====
    #     # Uncomment this entire section for real flight operations
    #     # Replace the testing block above with this

    #     if SM.current_state != STATES.EXPERIMENT:

    #         if not PC.interface_injected():
    #             PC.load_communication_interface()

    #         # Need to handle issues with power control eventually or log error codes for the HAL

    #         self.init_all_data_processes()

    #         # Two cases:
    #         #  - Satellite has booted up and we need to initialize the payload
    #         #  - State transitioned out of EXPERIMENT and we need to stop the payload gracefully
    #         #    (forcefully in worst-case scenarios)

    #         # TODO: This is going to change
    #         if PC.state != PayloadState.OFF:  # All good

    #             PC.add_request(ExternalRequest.TURN_OFF)

    #             if PC.state == PayloadState.SHUTTING_DOWN:
    #                 # TODO: check timeout just in case. However, this will be handled internally.
    #                 PC.add_request(ExternalRequest.FORCE_POWER_OFF)
    #                 pass

    #     else:  # EXPERIMENT state

    #         if PC.state == PayloadState.OFF:
    #             PC.add_request(ExternalRequest.TURN_ON)

    #         elif PC.state == PayloadState.READY:
    #             if DH.file_process_exists("img"):
    #                 # Check how many complete image files we have
    #                 complete_image_count = DH.get_file_count("img")

    #                 if complete_image_count < _NUM_IMG_TO_MAINTAIN_READY and not PC.file_transfer_in_progress():
    #                     self.log_info(
    #                         "Not enough images in memory "
    #                         f"({complete_image_count}/{_NUM_IMG_TO_MAINTAIN_READY}), requesting new image",
    #                     )
    #                     PC.add_request(ExternalRequest.REQUEST_IMAGE)
    #                     print("\n\n\n")

    #     # DO NOT EXPOSE THE LOGIC IN THE TASK and KEEP EVERYTHING INTERNAL
    #     PC.run_control_logic()
    #     self.log_info(f"Payload state: {map_state(PC.state)}")
    #     # ===== END FULL STATE MACHINE =====
