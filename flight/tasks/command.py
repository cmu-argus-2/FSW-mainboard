# Command task (C&DH)
# This task handles spacecraft state, board status, and state transitions.
# It also executes commands received from the ground station (TBD)

import time

from apps.telemetry.constants import CDH_IDX
from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from hal.configuration import SATELLITE


class Task(TemplateTask):

    name = "COMMAND"
    ID = 0x01

    # To be removed - kept until proper logging is implemented
    data_keys = [
        "TIME",
        "SC_STATE",
        "SD_AVAILABLE_STORAGE",
        "CURRENT_RAM_USAGE",
        "REBOOT_COUNT",
        "WATCHDOG_TIMER",
        "HAL_BITFLAGS",
        "COMMUNICATION_STATUS",
        "ADCS_STATUS",
        "EPS_STATUS",
    ]

    async def main_task(self):

        print(f"[{self.ID}][{self.name}] GLOBAL STATE: {SM.current_state}.")
