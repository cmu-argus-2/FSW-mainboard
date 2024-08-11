# Command task (C&DH)
# This task handles spacecraft state, board status, and state transitions.
# It also executes commands received from the ground station (TBD)

import time

from apps.telemetry.constants import CDH_IDX
from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STATES, STR_STATES
from hal.configuration import SATELLITE


class Task(TemplateTask):

    name = "COMMAND"
    ID = 0x01

    # To be removed - kept until proper logging is implemented
    data_keys = [
        "TIME",
        "SC_STATE",
        "SD_USAGE",
        "CURRENT_RAM_USAGE",
        "REBOOT_COUNT",
        "WATCHDOG_TIMER",
        "HAL_BITFLAGS",
        "COMMUNICATION_STATUS",
        "ADCS_STATUS",
        "EPS_STATUS",
    ]

    log_data = [0] * len(data_keys)
    data_format = "fbQIHHbbbb"

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
            print(f"[{self.ID}][{self.name}] SD card cleaned up.")

            HAL_DIAGNOSTICS = True
            # For now
            if DH.SD_scanned and HAL_DIAGNOSTICS:
                SM.switch_to(STATES.NOMINAL)
                print(f"[{self.ID}][{self.name}] Switching to NOMINAL state.")

        else:  # Run for all states

            if not DH.data_process_exists("cdh"):
                DH.register_data_process("cdh", self.data_keys, self.data_format, True, line_limit=100)

            self.log_data[CDH_IDX.TIME] = time.time()
            self.log_data[CDH_IDX.SC_STATE] = SM.current_state
            self.log_data[CDH_IDX.SD_USAGE] = DH.SD_usage()  # gets updated in the OBDH task
            self.log_data[CDH_IDX.CURRENT_RAM_USAGE] = 0
            self.log_data[CDH_IDX.REBOOT_COUNT] = 0
            self.log_data[CDH_IDX.WATCHDOG_TIMER] = 0
            self.log_data[CDH_IDX.HAL_BITFLAGS] = 0
            self.log_data[CDH_IDX.COMMUNICATION_STATUS] = 0
            self.log_data[CDH_IDX.ADCS_STATUS] = 0
            self.log_data[CDH_IDX.EPS_STATUS] = 0

            DH.log_data("cdh", self.log_data)

            # Command processing
            # TODO

        print(f"[{self.ID}][{self.name}] GLOBAL STATE: {STR_STATES[SM.current_state]}.")
        print(f"[{self.ID}][{self.name}] Stored files: {self.log_data[CDH_IDX.SD_USAGE]} bytes.")
