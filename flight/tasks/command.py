# Command task (C&DH)
# This task handles spacecraft state, board status, and state transitions.
# It also executes commands received from the ground station (TBD)

import gc
import time

import apps.command.processor as processor
from apps.adcs.consts import Modes
from apps.command import QUEUE_STATUS, CommandQueue
from apps.telemetry.constants import ADCS_IDX, CDH_IDX
from apps.time_processor.time_processor import TIME_PROCESSOR
from core import DataHandler as DH
from core import TemplateTask
from core import state_manager as SM
from core.states import STATES, STR_STATES
from hal.configuration import SATELLITE


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

        # TODO: Remove once a coil cell is found in the lab
        TIME_PROCESSOR.set_time(1741709997)
        self.boot_time = TIME_PROCESSOR.time()

    def get_memory_usage(self):
        return int(gc.mem_alloc() / self.total_memory * 100)

    async def main_task(self):
        if SM.current_state == STATES.STARTUP:  # Startup sequence
            # Must perform / check all startup tasks here (rtc, sd, etc.)

            # TODO: Verification checklist
            # Goal is to report error but still allow to switch to operations
            # Errors must be localized and not affect other tasks
            # Boot errors and system diagnostics must be logged

            # TODO: Deployment

            # HAL_DIAGNOSTICS
            time_since_boot = int(TIME_PROCESSOR.time()) - self.boot_time
            if DH.SD_SCANNED() and time_since_boot > 5:  # seconds into start-up
                if not DH.data_process_exists("cdh"):
                    data_format = "LbLbbbbb"
                    DH.register_data_process("cdh", data_format, True, data_limit=100000)

                if not DH.data_process_exists("cmd_logs"):
                    DH.register_data_process("cmd_logs", "LBB", True, data_limit=100000)

                SM.switch_to(STATES.DETUMBLING)
                self.log_info("Switching to DETUMBLING state.")

        else:
            # Code that executes in all states

            # ------------------------------------------------------------------------------------------------------------------------------------
            # STATE MACHINE
            # ------------------------------------------------------------------------------------------------------------------------------------

            if SM.current_state == STATES.DETUMBLING:
                # Check detumbling status from the ADCS
                if DH.data_process_exists("adcs"):
                    if DH.get_latest_data("adcs")[ADCS_IDX.MODE] != Modes.TUMBLING:
                        self.log_info("Detumbling complete - Switching to NOMINAL state.")
                        SM.switch_to(STATES.NOMINAL)

                # Detumbling timeout in case the ADCS is not working
                if SM.time_since_last_state_change > STATES.DETUMBLING_TIMEOUT_DURATION:
                    self.log_info("DETUMBLING timeout - Setting Detumbling Error Flag.")
                    # Set the detumbling issue flag in the NVM
                    self.log_data[CDH_IDX.DETUMBLING_ERROR_FLAG] = 1
                    self.log_info("Switching to NOMINAL state after DETUMBLING timeout.")
                    SM.switch_to(STATES.NOMINAL)

            elif SM.current_state == STATES.NOMINAL:
                pass
            elif SM.current_state == STATES.EXPERIMENT:
                pass
            elif SM.current_state == STATES.LOW_POWER:
                pass

            SM.update_time_in_state()

            # ------------------------------------------------------------------------------------------------------------------------------------
            # COMMAND PROCESSOR
            # ------------------------------------------------------------------------------------------------------------------------------------

            if CommandQueue.command_available():
                (cmd_id, cmd_arglist), queue_error_code = CommandQueue.pop_command()
                cmd_args = processor.unpack_command_arguments(cmd_id, cmd_arglist)

                if (
                    queue_error_code == QUEUE_STATUS.OK
                    and cmd_args != processor.CommandProcessingStatus.ARGUMENT_UNPACKING_FAILED
                ):
                    self.log_info(f"Processing command: {cmd_id} with args: {cmd_args}")
                    status, response_args = processor.process_command(cmd_id, *cmd_args)
                    processor.handle_command_execution_status(status, response_args)

                    # Log the command execution history
                    self.log_commands[0] = int(TIME_PROCESSOR.time())
                    self.log_commands[1] = cmd_id
                    self.log_commands[2] = status
                    DH.log_data("cmd_logs", self.log_commands)

            # Set CDH log data
            self.log_data[CDH_IDX.TIME] = int(TIME_PROCESSOR.time())
            self.log_data[CDH_IDX.SC_STATE] = SM.current_state
            self.log_data[CDH_IDX.SD_USAGE] = int(DH.SD_usage() / 1000)  # kb - gets updated in the OBDH task
            self.log_data[CDH_IDX.CURRENT_RAM_USAGE] = self.get_memory_usage()
            self.log_data[CDH_IDX.REBOOT_COUNT] = 0
            self.log_data[CDH_IDX.WATCHDOG_TIMER] = 0
            self.log_data[CDH_IDX.HAL_BITFLAGS] = 0

            # The detumbling error flag is set in the DETUMBLING state

            # Should always run
            DH.log_data("cdh", self.log_data)

        self.log_print_counter += 1
        if self.log_print_counter % self.frequency == 0:
            self.log_print_counter = 0
            self.log_info(f"Time: {int(TIME_PROCESSOR.time())}")
            self.log_info(f"Time since boot: {int(TIME_PROCESSOR.time()) - self.boot_time}")
            self.log_info(f"GLOBAL STATE: {STR_STATES[SM.current_state]}.")
            self.log_info(f"RAM USAGE: {self.log_data[CDH_IDX.CURRENT_RAM_USAGE]}%")
