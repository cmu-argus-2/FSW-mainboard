"""
monitor.py
================
Satellite monitoring task
"""

# Garbage collector and time
import gc
import time

from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH

# PyCubed Board Lib
from hal.configuration import SATELLITE


class Task(TemplateTask):

    name = "MONITOR"
    ID = 0x00

    data_keys = [
        "time",
        "system_status",
        "batt_soc",
        "current",
        "reboot_cnt",
    ]

    system_status = 0x00
    batt_soc = 0
    current = 0

    async def main_task(self):
        # Get power system readings
        (
            self.batt_soc,
            self.current,
        ) = SATELLITE.BATTERY_POWER_MONITOR.read_voltage_current()

        self.batt_soc = int(self.batt_soc * 100 / 8.4)
        self.current = int(self.current * 10000)

        # Read data for monitoring
        readings = {
            "time": time.time(),
            "system_status": 0,
            "batt_soc": self.batt_soc,
            "current": self.current,
            "reboot_cnt": 0,
        }

        if SM.current_state == "NOMINAL":
            # If process not registered, register it
            if not DH.data_process_exists("monitor"):
                DH.register_data_process("monitor", self.data_keys, "ffffb", True, line_limit=50)

            DH.log_data("monitor", readings)

            print(f"[{self.ID}][{self.name}] Data: {readings}")
            print(f"[{self.ID}][{self.name}] {gc.mem_free()} free bytes in memory")
