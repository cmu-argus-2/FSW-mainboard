import time

from apps.telemetry.constants import IMU_IDX
from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STATES
from hal.configuration import SATELLITE


class Task(TemplateTask):

    name = "IMU"
    ID = 0x03

    # To be removed - kept until proper logging is implemented
    data_keys = [
        "time",
        "accel_x",
        "accel_y",
        "accel_z",
        "mag_x",
        "mag_y",
        "mag_z",
        "gyro_x",
        "gyro_y",
        "gyro_z",
    ]

    # pre-allocation
    log_data = [0.0] * 10

    async def main_task(self):

        if SM.current_state == STATES.NOMINAL:

            if not DH.data_process_exists("imu"):
                DH.register_data_process("imu", self.data_keys, "Lfffffffff", True, line_limit=40)

            accel = SATELLITE.IMU.accel()
            mag = SATELLITE.IMU.mag()
            gyro = SATELLITE.IMU.gyro()

            # Replace data in the pre-allocated list
            self.log_data[IMU_IDX.TIME] = int(time.time())
            self.log_data[IMU_IDX.ACCEL_X] = accel[0]
            self.log_data[IMU_IDX.ACCEL_Y] = accel[1]
            self.log_data[IMU_IDX.ACCEL_Z] = accel[2]
            self.log_data[IMU_IDX.MAG_X] = mag[0]
            self.log_data[IMU_IDX.MAG_Y] = mag[1]
            self.log_data[IMU_IDX.MAG_Z] = mag[2]
            self.log_data[IMU_IDX.GYRO_X] = gyro[0]
            self.log_data[IMU_IDX.GYRO_Y] = gyro[1]
            self.log_data[IMU_IDX.GYRO_Z] = gyro[2]

            DH.log_data("imu", self.log_data)

            print(f"[{self.ID}][{self.name}] Data: {dict(zip(self.data_keys, self.log_data))}")
