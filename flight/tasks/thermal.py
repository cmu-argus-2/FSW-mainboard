# Thermal monitoring and control Task

import time

import microcontroller
from apps.telemetry.constants import THERMAL_IDX
from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STATES
from hal.configuration import SATELLITE


class Task(TemplateTask):

    data_keys = ["TIME", "IMU_TEMPERATURE", "CPU_TEMPERATURE", "BATTERY_PACK_TEMPERATURE"]

    log_data = [0] * 4  # pre-allocation
    data_format = "LHHH"

    async def main_task(self):

        if SM.current_state == STATES.NOMINAL:

            if not DH.data_process_exists("thermal"):
                DH.register_data_process("thermal", self.data_keys, self.data_format, True, line_limit=100)

            self.log_data[THERMAL_IDX.TIME] = int(time.time())
            self.log_data[THERMAL_IDX.IMU_TEMPERATURE] = int(SATELLITE.IMU.temperature() * 100)
            self.log_data[THERMAL_IDX.CPU_TEMPERATURE] = int(microcontroller.cpu.temperature * 100)
            self.log_data[THERMAL_IDX.BATTERY_PACK_TEMPERATURE] = 0  # Placeholder

            DH.log_data("thermal", self.log_data)

        self.log_info(
            f" CPU: {self.log_data[THERMAL_IDX.CPU_TEMPERATURE]/100}°, \
            IMU: {self.log_data[THERMAL_IDX.IMU_TEMPERATURE]/100}°"
        )
