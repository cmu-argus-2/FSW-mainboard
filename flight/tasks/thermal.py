# Thermal monitoring and control Task

import time

import microcontroller
from apps.telemetry.constants import THERMAL_IDX
from core import TemplateTask
from core import state_manager as SM


class Task(TemplateTask):

    name = "THERMAL"
    ID = 0x0A

    data_keys = ["TIME", "IMU_TEMPERATURE", "CPU_TEMPERATURE", "BATTERY_PACK_TEMPERATURE"]

    log_data = [0] * 4  # pre-allocation
    data_format = "fHHH"

    async def main_task(self):

        if SM.current_state == "NOMINAL":

            if not self.DH.data_process_exists("THERMAL"):
                self.DH.register_data_process("THERMAL", self.data_keys, self.data_format, True, line_limit=100)

            self.log_data[THERMAL_IDX.TIME] = time.time()
            self.log_data[THERMAL_IDX.IMU_TEMPERATURE] = int(self.IMU.temperature() * 100)
            self.log_data[THERMAL_IDX.CPU_TEMPERATURE] = int(microcontroller.cpu.temperature * 100)
            self.log_data[THERMAL_IDX.BATTERY_PACK_TEMPERATURE] = 0  # Placeholder

            self.log_data("THERMAL", self.log_data)

        print(
            f"[{self.ID}][{self.name}] CPU Temp: {self.log_data[THERMAL_IDX.CPU_TEMPERATURE]/100}° \
                                        IMU Temp: {self.log_data[THERMAL_IDX.IMU_TEMPERATURE]/100}°"
        )
