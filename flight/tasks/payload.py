# Payload Control Task

from apps.payload.controller import PayloadController as PC
from apps.telemetry.splat.splat.telemetry_codec import Command
from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.dh_constants import PAYLOAD_IDX
from core.states import STATES
from core.time_processor import TimeProcessor as TPM


class Task(TemplateTask):

    _last_state_print_ts = 0  # Track last time state was printed

    def __init__(self, id):
        super().__init__(id)
        self.name = "PAYLOAD"
        self.init_all_data_processes()

    def init_all_data_processes(self):

        # Telemetry process
        if not DH.data_process_exists("payload_tm"):
            DH.register_data_process(
                tag_name="payload_tm",
                data_format=PC.payload_tm_data_format,
                persistent=True,
                data_limit=100000,
                circular_buffer_size=200,
            )

    def run_idle_state(self):
        """
        This is the function that will run when the payload is in idle state
        It will be in idle state while it has no commands to be processed
        It will simply look at the the command list to see if there are any commands
            if there are commands, it will change to watching state
        If there are no commands, it will just return
        """

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

        """

        command = PC.get_first_command()
        self.log_info(f"Watching for command: {command}")

        # update next command time
        PC.log_data[PAYLOAD_IDX.NEXT_CMD_TIME] = command[0]

        # check to see if the time to execute the command has arrived
        if command[0] < TPM.time() or command[0] == 0:
            # means that it is time to run the command
            self.log_info("Command time has arrived, switching to booting state.")
            PC.BOOT_TS = TPM.time()
            PC.received_ping_ack = False

            status = PC.switch_state("BOOTING")
            if not status:
                self.log_warning("Failed to switch to BOOTING state.")
                PC.switch_state("FAIL")
                return
            return

        # not time to run the command yet
        return

    def run_booting_state(self):
        """
        This state will be responsible for making sure that the jetson boots up
        the jetson will be turned on in the change state function to guarantee that we are only doing it once
        after that, every time this runs it will send a ping command and wait for a response
            once it has received a response it will move state ACTIVE
        it has a timeout where it will go to fail state and turn of the jetson
        The command has been choosen when switched to this state to make sure that if boots fails, it will
        not attempt to run the command again
        """

        # check to see if we got response from ping
        if PC.received_ping_ack:
            # means we have received a response from jetson, moving to ACTIVE state
            self.log_info("Ping responded, switching to ACTIVE state.")
            PC.received_experiment_ack = False
            PC.ACT_TS = TPM.time()
            PC.switch_state("ACTIVE")

            # set the last_executed_time
            PC.log_data[PAYLOAD_IDX.LAST_EXECUTED_CMD_TIME] = TPM.time()

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
        command has already been choosen and removed from the list when it switched to boot state
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

        if PC.ACT_TS + PC.ACT_TIMEOUT <= TPM.time():
            self.log_error("Active timeout reached, switching to FAIL state.")
            PC.switch_state("FAIL")
            return

        # send the command
        # TODO - only want to send this every 5 seconds for example
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
            PC.send_telemetry_command()  # request for telemetry value to get the inference return
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
        self.log_info("Finished state reached.")

        # move directly to download state
        PC.DWN_TS = TPM.time()
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
        if PC.DWN_LAST_FRAGMENT_TS + PC.DWN_TIMEOUT <= TPM.time():
            self.log_error("Download fragment timeout reached, switching to FAIL state.")
            PC.switch_state("FAIL")
            return

        # If no transactions to process yet, wait for them
        if not PC.received_create_trans or not PC.received_init_trans:
            return

        # Get current download status
        status = PC.get_download_status()

        # Only leave DOWNLOAD when the payload explicitly reports that all files were sent
        if not status["has_active_file"]:
            if PC.received_all_files_sent:
                self.log_info("Payload reported all files sent, transitioning to OFF state.")
                PC.switch_state("OFF")
                PC.OFF_TS = TPM.time()
            else:
                self.log_info("No active file right now; waiting for next file or completion signal from payload.")
            return

        try:
            # Process one batch: listen, save, generate bitmap
            bitmap_high, bitmap_low = PC.download_manager.process_batch(PC.process_uart)

            if bitmap_high is None or bitmap_low is None:
                return

            status = PC.get_download_status()

            # Send confirmation to jetson
            command = Command("CONFIRM_LAST_BATCH")
            command.add_argument("tid", status["current_tid"])
            command.add_argument("bitmap_high", bitmap_high)
            command.add_argument("bitmap_low", bitmap_low)
            PC.send_confirm_last_batch(command)

            self.log_info(
                f"Sent CONFIRM_LAST_BATCH: tid={status['current_tid']},"
                + f" bitmap_high=0x{bitmap_high:08X}, bitmap_low=0x{bitmap_low:08X},"
                + f" missing={status['missing_fragments']}"
            )

            # Check if file is complete
            if PC.download_manager.is_file_complete():
                self.log_info(f"File complete for tid={status['current_tid']}, finalizing...")

                # Finalize current file (write, verify, cleanup)
                if PC.download_manager.finalize_file():
                    self.log_info(f"File finalized successfully for tid={status['current_tid']}")

                    # Move to next file in queue
                    if PC.download_manager.advance_to_next_file():
                        self.log_info("Advanced to next file in queue")
                    else:
                        self.log_info(
                            "No more files currently queued; waiting for payload to send next file or completion signal"
                        )
                else:
                    self.log_error(f"Failed to finalize file for tid={status['current_tid']}")
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

        TODO: instead of having fixed time here, read the values reported from jetson current sensor
            will still need to have a timeout
        """

        if PC.received_off_ack and not PC.waiting_shutdown:
            # we have received response from jetson, safe to turn off
            self.log_info("Received off ack, starting 20 sec wait to cut power")
            PC.OFF_TS = TPM.time()  # received the ack, lets give it time to shut down
            PC.waiting_shutdown = True

        if PC.OFF_TS + PC.OFF_TIMEOUT <= TPM.time():
            self.log_info("Turn off timeout reached, cutting power to jetson.")
            PC.turn_off_power()
            if PC.received_off_ack:
                PC.received_off_ack = False
                PC.switch_state("SUCCESS")  # receive the shutdown ack, gave time and can cut power now
            else:
                PC.switch_state("FAIL")  # did not received the shutdown ack, failing and forcing to shutdown

    def run_success_state(self):
        """
        This state will only be reached when the experiment has been succesfully completed
        it will just be used to send a message to the groundstation to let them know that
        the experiment has finished.
        That will be done in the switch state function. Here we will only move on to idle
        """

        self.log_info("Experiment completed successfully. Going to idle")
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

        # Do not run in startup
        if SM.current_state == STATES.STARTUP:
            return

        if TPM.time() - self._last_state_print_ts >= 5:
            self._last_state_print_ts = TPM.time()
            DH.log_data("payload_tm", PC.log_data)  # periodically log data
            self.log_info(f"Current state: {PC.current_state}")
            self.log_info(f"  next command time: {PC.log_data[PAYLOAD_IDX.NEXT_CMD_TIME]}")

        if SM.current_state == STATES.LOW_POWER:
            # we are in low power mode, will not run the payload task
            # and will fail if I was in another state other then idle
            if PC.current_state != 0:
                self.log_warning("In LOW POWER state but payload is not in IDLE state, switching to fail.")
                PC.switch_state("FAIL")  # this will send the fail message to gs and change to idle
                self.run_fail_state()  # this will cut the power to the jetson and change to idle
            return

        if PC.current_state == 0:
            self.run_idle_state()
            return  # prevent from reading from uart when not necessary
        if PC.current_state == 1:
            self.run_watching_state()
            return  # prevent from reading from uart when not necessary
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
            self.run_success_state()
        if PC.current_state == 9:
            self.run_fail_state()

        # TODO - do i really want to have this
        PC.process_uart()
