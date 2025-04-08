# Command task (C&DH)
# This task handles spacecraft state, board status, and state transitions.
# It also executes commands received from the ground station (TBD)

import gc

import apps.command.processor as processor
from apps.adcs.consts import Modes
from apps.command import QUEUE_STATUS, CommandQueue
from apps.eps.eps import EPS_POWER_FLAG
from apps.telemetry.constants import ADCS_IDX, CDH_IDX, EPS_IDX
from core import DataHandler as DH
from core import TemplateTask
from core import state_manager as SM
from core.states import STATES, STR_STATES
from core.time_processor import TimeProcessor as TPM
from hal.configuration import SATELLITE
from micropython import const

_TPM_INIT_TIMEOUT = const(10)  # seconds
_EXIT_STARTUP_TIMEOUT = const(5)  # seconds


class Task(TemplateTask):
    # To be removed
    # data_keys = ["TIME", "SC_STATE", "SD_USAGE", "CURRENT_RAM_USAGE", "REBOOT_COUNT",
    # "WATCHDOG_TIMER", "HAL_BITFLAGS", "DETUMBLING_ERROR_FLAG"]

    log_data = [0] * 8

    log_commands = [0] * 3

    gc.collect()
    total_memory = gc.mem_alloc() + gc.mem_free()

    log_print_counter = 0

    def __init__(self, id):
        super().__init__(id)
        self.name = "COMMAND"
        self.time_ref_set = False

        # Transition status from ADCS and EPS
        self.ADCS_MODE = Modes.STABLE
        self.EPS_MODE = EPS_POWER_FLAG.NOMINAL

    def get_memory_usage(self):
        return int(gc.mem_alloc() / self.total_memory * 100)

    def startup(self):
        # ------------------------------------------------------------------------------------------------------------------------------------
        # STARTUP SEQUENCE
        # ------------------------------------------------------------------------------------------------------------------------------------

        # Must perform / check all startup tasks here (rtc, sd, etc.)

        # TODO: Verification checklist
        # Goal is to report error but still allow to switch to operations
        # Errors must be localized and not affect other tasks
        # Boot errors and system diagnostics must be logged

        # Neopixel for STARTUP (white)
        if SATELLITE.NEOPIXEL_AVAILABLE:
            SATELLITE.NEOPIXEL.fill([255, 255, 255])

        # TODO: Deployment

        # Check time_since_boot
        time_since_boot = TPM.monotonic() - SATELLITE.BOOTTIME

        # NOTE: TPM time reference initialization
        # In case the RTC has died, TPM uses time reference for time keeping
        # The time reference is used to get offset from time.time()

        # If an old time reference is not available, we depend on state correction
        # from GPS or uplinked commands, and until then the time will be egregiously wrong

        # This will not work until OBDH initializes CDH data process, so try for 10 seconds
        # since the SC has booted

        if time_since_boot < _TPM_INIT_TIMEOUT and SATELLITE.RTC_AVAILABLE is False and self.time_ref_set is False:
            # Only worth it if the RTC is dead
            if DH.data_process_exists("cdh"):
                cdh_data = DH.get_latest_data("cdh")

                if cdh_data:
                    # Found an old timestamp reference
                    TPM.set_time(cdh_data[CDH_IDX.TIME])
                    self.time_ref_set = True
                    self.log_info(f"Updated time reference for TPM: {TPM.time()}")

                else:
                    # If no RTC or old time reference available, TPM goes back to Jan 1st 2025
                    self.log_warning("Cannot set time reference as CDH process has no latest data")
            else:
                # If no RTC or old time reference available, TPM goes back to Jan 1st 2025
                self.log_warning("Cannot set time reference as CDH process does not exist")

            if time_since_boot == _TPM_INIT_TIMEOUT - 1:
                # Failed in initializing TPM, just initialize offset calculation
                TPM.calc_time_offset()

        else:
            # If the DH successfully scanned the SD card, and it has been 5 secs since FSW boot
            if DH.SD_SCANNED() and time_since_boot > _EXIT_STARTUP_TIMEOUT:
                if not DH.data_process_exists("cdh"):
                    data_format = "LbLbbbbb"
                    DH.register_data_process("cdh", data_format, True, data_limit=100000)

                if not DH.data_process_exists("cmd_logs"):
                    DH.register_data_process("cmd_logs", "LBB", True, data_limit=100000)

                # T0: Boot over and deployment complete
                SM.switch_to(STATES.DETUMBLING)
                self.log_info("Switching to DETUMBLING state.")

    def state_machine_execution(self):
        # ------------------------------------------------------------------------------------------------------------------------------------
        # STATE MACHINE
        # ------------------------------------------------------------------------------------------------------------------------------------

        # Get ADCS mode (hysteresis management done in ADCS application)
        if DH.data_process_exists("adcs"):
            adcs_data = DH.get_latest_data("adcs")

            if adcs_data:
                self.ADCS_MODE = adcs_data[ADCS_IDX.MODE]
            else:
                self.log_warning("No latest ADCS data available, assuming STABLE ADCS mode")
                self.ADCS_MODE = Modes.STABLE
        else:
            self.log_warning("ADCS task not available, assuming STABLE ADCS mode")
            self.ADCS_MODE = Modes.STABLE

        # Get EPS mode (hysteresis management done in EPS application)
        if DH.data_process_exists("eps"):
            eps_data = DH.get_latest_data("eps")

            if eps_data:
                self.EPS_MODE = eps_data[EPS_IDX.EPS_POWER_FLAG]
            else:
                self.log_warning("No latest EPS data available, assuming NOMINAL EPS mode")
                self.EPS_MODE = EPS_POWER_FLAG.NOMINAL
        else:
            self.log_warning("EPS task not available, assuming NOMINAL EPS mode")
            self.EPS_MODE = EPS_POWER_FLAG.NOMINAL

        # ------------------------------------------------------------------------------------------------------------------------------------
        # DETUMBLING
        # ------------------------------------------------------------------------------------------------------------------------------------

        if SM.current_state == STATES.DETUMBLING:
            # Neopixel for DETUMBLING (orange)
            if SATELLITE.NEOPIXEL_AVAILABLE:
                SATELLITE.NEOPIXEL.fill([255, 165, 0])

            # Detumbling timeout in case the ADCS is not working
            if SM.time_since_last_state_change > STATES.DETUMBLING_TIMEOUT_DURATION:
                self.log_info("DETUMBLING timeout - Setting Detumbling Error Flag.")
                # Set the detumbling issue flag in the NVM
                self.log_data[CDH_IDX.DETUMBLING_ERROR_FLAG] = 1

            if self.ADCS_MODE != Modes.TUMBLING or self.log_data[CDH_IDX.DETUMBLING_ERROR_FLAG] == 1:
                # T1.1: Spin stabilized OR detumbling error flag is set (detumbling timeout)
                self.log_info("T1.1: Transition from DETUMBLING to NOMINAL")
                SM.switch_to(STATES.NOMINAL)

            if self.EPS_MODE == EPS_POWER_FLAG.LOW_POWER:
                # T1.2: Low SoC, transition to low power
                self.log_info("T1.2: Transition from DETUMBLING to LOW POWER")
                SM.switch_to(STATES.LOW_POWER)

        # ------------------------------------------------------------------------------------------------------------------------------------
        # NOMINAL
        # ------------------------------------------------------------------------------------------------------------------------------------

        elif SM.current_state == STATES.NOMINAL:
            # Neopixel for NOMINAL (green)
            if SATELLITE.NEOPIXEL_AVAILABLE:
                SATELLITE.NEOPIXEL.fill([0, 255, 0])

            if self.EPS_MODE == EPS_POWER_FLAG.EXPERIMENT:
                # T2.1: High SoC, engage the payload
                self.log_info("T2.1: Transition from NOMINAL to EXPERIMENT")
                SM.switch_to(STATES.EXPERIMENT)

            if self.EPS_MODE == EPS_POWER_FLAG.LOW_POWER:
                # T2.2: Low SoC, transition to low power
                self.log_info("T2.2: Transition from NOMINAL to LOW POWER")
                SM.switch_to(STATES.LOW_POWER)

            if self.ADCS_MODE == Modes.TUMBLING and self.log_data[CDH_IDX.DETUMBLING_ERROR_FLAG] != 1:
                # T2.3: Tumbling again AND detumbling error flag is not set
                self.log_info("T2.3: Transition from NOMINAL to DETUMBLING")
                SM.switch_to(STATES.DETUMBLING)

        # ------------------------------------------------------------------------------------------------------------------------------------
        # LOW POWER
        # ------------------------------------------------------------------------------------------------------------------------------------

        elif SM.current_state == STATES.LOW_POWER:
            # Neopixel for LOW_POWER (red)
            if SATELLITE.NEOPIXEL_AVAILABLE:
                SATELLITE.NEOPIXEL.fill([255, 0, 0])

            if self.EPS_MODE != EPS_POWER_FLAG.LOW_POWER:
                # T3.1: Nominal or high SoC, transition out of low power
                self.log_info("T3.1: Transition from LOW POWER to NOMINAL")
                SM.switch_to(STATES.NOMINAL)

        # ------------------------------------------------------------------------------------------------------------------------------------
        # PAYLOAD / EXPERIMENT
        # ------------------------------------------------------------------------------------------------------------------------------------

        elif SM.current_state == STATES.EXPERIMENT:
            # Neopixel for PAYLOAD / EXPERIMENT (purple)
            if SATELLITE.NEOPIXEL_AVAILABLE:
                SATELLITE.NEOPIXEL.fill([255, 0, 255])

            if self.EPS_MODE != EPS_POWER_FLAG.EXPERIMENT:
                # T4.1: Nominal or low SoC, transition back to nominal
                self.log_info("T4.1: Transition from LOW POWER to NOMINAL")
                SM.switch_to(STATES.NOMINAL)

        # ------------------------------------------------------------------------------------------------------------------------------------
        # CRITICAL ERROR - UNKNOWN STATE
        # ------------------------------------------------------------------------------------------------------------------------------------

        else:
            self.log_error("CRITICAL: Argus is in an unknown state")

        SM.update_time_in_state()

    def command_processor_execution(self):
        # ------------------------------------------------------------------------------------------------------------------------------------
        # COMMAND PROCESSOR
        # ------------------------------------------------------------------------------------------------------------------------------------

        if CommandQueue.command_available():
            (cmd_id, cmd_arglist), queue_error_code = CommandQueue.pop_command()
            cmd_args = processor.unpack_command_arguments(cmd_id, cmd_arglist)

            if queue_error_code == QUEUE_STATUS.OK and cmd_args != processor.CommandProcessingStatus.ARGUMENT_UNPACKING_FAILED:
                self.log_info(f"Processing command: {cmd_id} with args: {cmd_args}")
                status, response_args = processor.process_command(cmd_id, *cmd_args)
                processor.handle_command_execution_status(status, response_args)

                # Log the command execution history
                self.log_commands[0] = TPM.time()
                self.log_commands[1] = cmd_id
                self.log_commands[2] = status
                DH.log_data("cmd_logs", self.log_commands)

    async def main_task(self):
        if SM.current_state == STATES.STARTUP:
            # Startup sequence
            self.startup()

        else:
            # Run command processor
            self.command_processor_execution()

            # Execute state machine
            self.state_machine_execution()

            # Set CDH log data
            self.log_data[CDH_IDX.TIME] = TPM.time()
            self.log_data[CDH_IDX.SC_STATE] = SM.current_state
            self.log_data[CDH_IDX.SD_USAGE] = int(DH.SD_usage() / 1000)  # kb - gets updated in the OBDH task
            self.log_data[CDH_IDX.CURRENT_RAM_USAGE] = self.get_memory_usage()
            self.log_data[CDH_IDX.REBOOT_COUNT] = 0
            self.log_data[CDH_IDX.WATCHDOG_TIMER] = 0
            self.log_data[CDH_IDX.HAL_BITFLAGS] = 0

            # The detumbling error flag is set in the DETUMBLING state

            # Should always run
            DH.log_data("cdh", self.log_data)

        # Periodically log to serial
        self.log_print_counter += 1

        if self.log_print_counter % self.frequency == 0:
            self.log_print_counter = 0

            self.log_info(f"Time: {TPM.time()}")
            self.log_info(f"Time since boot: {TPM.monotonic() - SATELLITE.BOOTTIME}")
            self.log_info(f"GLOBAL STATE: {STR_STATES[SM.current_state]}.")
            self.log_info(f"RAM USAGE: {self.log_data[CDH_IDX.CURRENT_RAM_USAGE]}%")
