# Sun Vector Tasks

import time

from apps.adcs.sun import SUN_VECTOR_STATUS, compute_body_sun_vector_from_lux, in_eclipse, read_light_sensors
from apps.telemetry.constants import SUN_IDX
from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STATES
from ulab import numpy as np


class Task(TemplateTask):

    name = "SUN"
    ID = 0x11

    # To be removed - kept until proper logging is implemented
    data_keys = ["time", "status", "x", "y", "z", "eclipse"]

    THRESHOLD_ILLUMINATION_LUX = 3000

    status = SUN_VECTOR_STATUS.NO_READINGS
    sun_vector = np.zeros(3)
    eclipse_state = False

    # pre-allocation
    log_data = [0] * 6

    async def main_task(self):

        if SM.current_state == STATES.NOMINAL:

            if not DH.data_process_exists("sun"):
                DH.register_data_process("sun", self.data_keys, "Lbfffb", True, line_limit=100)

            # Access Sun Sensor Readings - Satellite must return the array directly
            lux_readings = read_light_sensors()

            self.status, self.sun_vector = compute_body_sun_vector_from_lux(lux_readings)
            self.eclipse_state = in_eclipse(
                lux_readings,
                threshold_lux_illumination=self.THRESHOLD_ILLUMINATION_LUX,
            )

            self.log_data[SUN_IDX.TIME] = int(time.time())
            self.log_data[SUN_IDX.STATUS] = self.status
            self.log_data[SUN_IDX.X] = self.sun_vector[0]
            self.log_data[SUN_IDX.Y] = self.sun_vector[1]
            self.log_data[SUN_IDX.Z] = self.sun_vector[2]
            self.log_data[SUN_IDX.ECLIPSE] = self.eclipse_state

            DH.log_data("sun", self.log_data)
            print(f"[{self.ID}][{self.name}] Data: {dict(zip(self.data_keys, self.log_data))}")
