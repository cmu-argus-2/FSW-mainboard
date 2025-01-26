# Command task (C&DH)
# This task handles spacecraft state, board status, and state transitions.
# It also executes commands received from the ground station (TBD)

import gc
import time

from apps.adcs.modes import Modes
from apps.command import QUEUE_STATUS, CommandQueue
from apps.command.constants import CMD_ID
from apps.command.processor import handle_command_execution_status, process_command
from apps.telemetry.constants import ADCS_IDX, CDH_IDX
from apps.telemetry.helpers import unpack_unsigned_long_int
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

    def get_memory_usage(self):
        return int(gc.mem_alloc() / self.total_memory * 100)

    async def main_task(self):
        if SM.current_state == STATES.STARTUP:
            # Must perform / check all startup tasks here (rtc, sd, etc.)

            # TODO
            # verification checklist
            # Goal is to report error but still allow to switch to operations
            # Errors must be localized and not affect other tasks
            # Boot errors and system diagnostics must be logged

            ### RTC setup

            # r = rtc.RTC()
            SATELLITE.RTC.set_datetime(time.struct_time((2024, 4, 24, 9, 30, 0, 3, 115, -1)))
            # rtc.set_time_source(r)

            # TODO: Burn wires

            # HAL_DIAGNOSTICS
            time_since_boot = int(time.time()) - SATELLITE.BOOTTIME
            if DH.SD_SCANNED() and time_since_boot > 5:  # seconds into start-up
                if not DH.data_process_exists("cdh"):
                    data_format = "LbLbbbbb"
                    DH.register_data_process("cdh", data_format, True, data_limit=100000)

                if not DH.data_process_exists("cmd_logs"):
                    DH.register_data_process("cmd_logs", "LBB", True, data_limit=100000)

                SM.switch_to(STATES.DETUMBLING)
                self.log_info("Switching to DETUMBLING state.")

                # Just for testing
                # CommandQueue.push_command(0x40, [])

                # Testing single-element queue
                # CommandQueue.overwrite_command(0x01,[STATES.LOW_POWER, 0x00])
                # CommandQueue.overwrite_command(0x41,[STATES.DETUMBLING, 0x00])  #should only execute this with overwrite
        else:  # Run for all other states
            ### STATE MACHINE ###
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

            ### COMMAND PROCESSING ###

            if CommandQueue.command_available():
                (cmd_id, cmd_arglist), queue_error_code = CommandQueue.pop_command()
                # self.log_info(f"ID: {cmd_id} Arguments: {cmd_args}")

                # TODO: Move to another function
                # Unpack arguments based on message ID
                if cmd_id == CMD_ID.SWITCH_TO_STATE:
                    cmd_arglist = list(cmd_arglist)
                    cmd_args = [0x00, 0x00]
                    cmd_args[0] = cmd_arglist[0]
                    cmd_args[1] = unpack_unsigned_long_int(cmd_arglist[1:5])

                    self.log_info(f"ID: {cmd_id} Argument List: {cmd_args}")
                else:
                    cmd_args = []

                if queue_error_code == QUEUE_STATUS.OK:
                    self.log_info(f"Processing command: {cmd_id} with args: {cmd_args}")
                    status, response_args = process_command(cmd_id, *cmd_args)

                    handle_command_execution_status(status, response_args)

                    # Log the command execution history
                    self.log_commands[0] = int(time.time())
                    self.log_commands[1] = cmd_id
                    self.log_commands[2] = status
                    DH.log_data("cmd_logs", self.log_commands)

            self.log_data[CDH_IDX.TIME] = int(time.time())
            self.log_data[CDH_IDX.SC_STATE] = SM.current_state
            self.log_data[CDH_IDX.SD_USAGE] = int(DH.SD_usage() / 1000)  # kb - gets updated in the OBDH task
            self.log_data[CDH_IDX.CURRENT_RAM_USAGE] = self.get_memory_usage()
            self.log_data[CDH_IDX.REBOOT_COUNT] = 0
            self.log_data[CDH_IDX.WATCHDOG_TIMER] = 0
            self.log_data[CDH_IDX.HAL_BITFLAGS] = 0
            # the detumbling error flag is set in the DETUMBLING state

            # Should always run
            DH.log_data("cdh", self.log_data)

        self.log_print_counter += 1
        if self.log_print_counter % self.frequency == 0:
            self.log_print_counter = 0
            self.log_info(f"Time: {int(time.time())}")
            self.log_info(f"Time since boot: {int(time.time()) - SATELLITE.BOOTTIME}")
            self.log_info(f"GLOBAL STATE: {STR_STATES[SM.current_state]}.")
            self.log_info(f"RAM USAGE: {self.log_data[CDH_IDX.CURRENT_RAM_USAGE]}%")
