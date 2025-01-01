# Command task (C&DH)
# This task handles spacecraft state, board status, and state transitions.
# It also executes commands received from the ground station (TBD)

import gc
import time

from apps.command import CommandQueue
from apps.command.processor import handle_command_execution_status, process_command
from apps.telemetry.constants import CDH_IDX
from core import DataHandler as DH
from core import TemplateTask
from core import state_manager as SM
from core.states import STATES, STR_STATES
from hal.configuration import SATELLITE


class Task(TemplateTask):

    # To be removed
    # data_keys = ["TIME", "SC_STATE", "SD_USAGE", "CURRENT_RAM_USAGE", "REBOOT_COUNT", "WATCHDOG_TIMER", "HAL_BITFLAGS"]

    log_data = [0] * 7

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

            HAL_DIAGNOSTICS = True  # TODO For now

            if DH.SD_scanned and HAL_DIAGNOSTICS:

                if not DH.data_process_exists("cdh"):
                    data_format = "LbLbbbb"
                    DH.register_data_process("cdh", data_format, True, data_limit=100000)

                if not DH.data_process_exists("cmd_logs"):
                    DH.register_data_process("cmd_logs", "LBB", True, data_limit=100000)

                SM.switch_to(STATES.NOMINAL)
                self.log_info("Switching to NOMINAL state.")

                # CommandQueue.push_command(0x01, [])
                # CommandQueue.push_command(0x02, [])

        else:  # Run for all states

            ### COMMAND PROCESSING ###

            if CommandQueue.command_available():

                (cmd_id, cmd_args), queue_error_code = CommandQueue.pop_command()

                if queue_error_code == CommandQueue.OK:

                    self.log_info(f"Processing command: {cmd_id} with args: {cmd_args}")
                    status = process_command(cmd_id, *cmd_args)

                    handle_command_execution_status(status)

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

            DH.log_data("cdh", self.log_data)

            # Burn wires

            # Handle middleware flags / HW states

            # periodic system checks (HW) - better another task for this

        self.log_print_counter += 1
        if self.log_print_counter % self.frequency == 0:
            self.log_print_counter = 0
            self.log_info(f"Time: {int(time.time())}")
            self.log_info(f"Time since boot: {int(time.time()) - SATELLITE.BOOTTIME}")
            self.log_info(f"GLOBAL STATE: {STR_STATES[SM.current_state]}.")
            self.log_info(f"RAM USAGE: {self.log_data[CDH_IDX.CURRENT_RAM_USAGE]}%")
