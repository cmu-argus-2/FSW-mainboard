# Thermal monitoring and control Task

import time

import microcontroller
from apps.telemetry.constants import THERMAL_IDX
from core import DataHandler as DH
from core import TemplateTask
from core import state_manager as SM
from core.states import STATES


class Task(TemplateTask):

    # data_keys = ["TIME", "IMU_TEMPERATURE", "CPU_TEMPERATURE", "BATTERY_PACK_TEMPERATURE"]

    log_data = [0] * 4  # pre-allocation

    def __init__(self, id):
        super().__init__(id)
        self.name = "THERMAL"

    async def main_task(self):

        if SM.current_state == STATES.NOMINAL:

            if not DH.data_process_exists("thermal"):
                DH.register_data_process("thermal", "LHHH", True, data_limit=100000, write_interval=10)

            # TODO: Make a better interface to the IMU's temperature sensor
            self.log_data[THERMAL_IDX.TIME_THERMAL] = int(time.time())
            self.log_data[THERMAL_IDX.IMU_TEMPERATURE] = 11 * 100
            self.log_data[THERMAL_IDX.CPU_TEMPERATURE] = int(microcontroller.cpu.temperature * 100)
            self.log_data[THERMAL_IDX.BATTERY_PACK_TEMPERATURE] = 0  # Placeholder

            DH.log_data("thermal", self.log_data)

        self.log_info(
            f" CPU: {self.log_data[THERMAL_IDX.CPU_TEMPERATURE] / 100}°, \
            IMU: {self.log_data[THERMAL_IDX.IMU_TEMPERATURE] / 100}°"
        )
