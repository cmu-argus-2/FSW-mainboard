# Command task (C&DH)
# This task handles spacecraft state, board status, and state transitions.
# It also executes commands received from the ground station (TBD)

import gc
import time

from apps.telemetry.constants import CDH_IDX
from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STATES, STR_STATES


class Task(TemplateTask):

    # To be removed - kept until proper logging is implemented
    data_keys = ["TIME", "SC_STATE", "SD_USAGE", "CURRENT_RAM_USAGE", "REBOOT_COUNT", "WATCHDOG_TIMER", "HAL_BITFLAGS"]

    log_data = [0] * len(data_keys)
    data_format = "LbLbbbb"

    gc.collect()
    total_memory = gc.mem_alloc() + gc.mem_free()

    def get_memory_usage(self):
        return int(gc.mem_alloc() / self.total_memory * 100)

    async def main_task(self):

        if SM.current_state == STATES.STARTUP:
            # Must perform / check all startup tasks here (rtc, sd, etc.)

            # TODO
            # verification checklist  TODO: Add more checks
            # Goal is to report error but still allow to switch to operations
            # Errors must be localized and not affect other tasks
            # Boot errors and system diagnostics

            # TODO: remove for flight
            DH.delete_all_files()
            self.log_info("SD card cleaned up.")

            HAL_DIAGNOSTICS = True
            # For now
            if DH.SD_scanned and HAL_DIAGNOSTICS:
                SM.switch_to(STATES.NOMINAL)
                self.log_info("Switching to NOMINAL state.")

        else:  # Run for all states

            if not DH.data_process_exists("cdh"):
                DH.register_data_process("cdh", self.data_keys, self.data_format, True, data_limit=100000)

            # gc.collect()

            self.log_data[CDH_IDX.TIME] = int(time.time())
            self.log_data[CDH_IDX.SC_STATE] = SM.current_state
            self.log_data[CDH_IDX.SD_USAGE] = int(DH.SD_usage() / 1000)  # kb - gets updated in the OBDH task
            self.log_data[CDH_IDX.CURRENT_RAM_USAGE] = self.get_memory_usage()
            self.log_data[CDH_IDX.REBOOT_COUNT] = 0
            self.log_data[CDH_IDX.WATCHDOG_TIMER] = 0
            self.log_data[CDH_IDX.HAL_BITFLAGS] = 0

            DH.log_data("cdh", self.log_data)

            # Command processing
            # TODO

            # Burn wires

            # Handle middleware flags / HW states

            # periodic system checks (HW) - better another task for this

        self.log_info(f"GLOBAL STATE: {STR_STATES[SM.current_state]}.")
        self.log_info(f"RAM USAGE: {self.log_data[CDH_IDX.CURRENT_RAM_USAGE]}%")
