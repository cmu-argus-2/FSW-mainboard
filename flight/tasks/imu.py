import time

from apps.telemetry.constants import IMU_IDX
from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from hal.configuration import SATELLITE


class Task(TemplateTask):

    name = "IMU"
    ID = 0x03

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

    _log_data = {
        IMU_IDX.TIME: time.time(),
        IMU_IDX.ACCEL_X: 0.0,
        IMU_IDX.ACCEL_Y: 0.0,
        IMU_IDX.ACCEL_Z: 0.0,
        IMU_IDX.MAG_X: 0.0,
        IMU_IDX.MAG_Y: 0.0,
        IMU_IDX.MAG_Z: 0.0,
        IMU_IDX.GYRO_X: 0.0,
        IMU_IDX.GYRO_Y: 0.0,
        IMU_IDX.GYRO_Z: 0.0,
    }

    async def main_task(self):

        if SM.current_state == "NOMINAL":

            if not DH.data_process_exists("imu"):
                DH.register_data_process("imu", self.data_keys, "ffffffffff", True, line_limit=40)

            accel = SATELLITE.IMU.accel()
            mag = SATELLITE.IMU.mag()
            gyro = SATELLITE.IMU.gyro()

            log_data = {
                "time": time.time(),
                "accel_x": accel[0],
                "accel_y": accel[1],
                "accel_z": accel[2],
                "mag_x": mag[0],
                "mag_y": mag[1],
                "mag_z": mag[2],
                "gyro_x": gyro[0],
                "gyro_y": gyro[1],
                "gyro_z": gyro[2],
            }

            DH.log_data("imu", log_data)

            print(f"[{self.ID}][{self.name}] Data: {log_data}")
