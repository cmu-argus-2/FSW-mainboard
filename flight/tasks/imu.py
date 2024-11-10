import time

from apps.telemetry.constants import IMU_IDX
from core import DataHandler as DH
from core import TemplateTask
from core import state_manager as SM
from core.states import STATES
from hal.configuration import SATELLITE
from hal.drivers.adafruit_bno08x import BNO_REPORT_ACCELEROMETER, BNO_REPORT_GYROSCOPE, BNO_REPORT_MAGNETOMETER
from micropython import const


class Task(TemplateTask):

    # To be removed - kept until proper logging is implemented
    """data_keys = [
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
    ]"""

    # pre-allocation
    log_data = [0.0] * 10
    log_print_counter = 0

    def __init__(self, id):
        super().__init__(id)
        self.name = "IMU"

    async def main_task(self):
        if SM.current_state == STATES.NOMINAL:

            if not DH.data_process_exists("imu"):
                DH.register_data_process("imu", "Lfffffffff", True, data_limit=100000, write_interval=5)

            if SATELLITE.IMU_NAME == "BNO08X":
                accel = SATELLITE.IMU.acceleration
                mag = SATELLITE.IMU.magnetic
                gyro = SATELLITE.IMU.gyro
            elif SATELLITE.IMU_NAME == "BMX160":
                accel = SATELLITE.IMU.accel()
                mag = SATELLITE.IMU.mag()
                gyro = SATELLITE.IMU.gyro()

            # Replace data in the pre-allocated list
            self.log_data[IMU_IDX.TIME_IMU] = int(time.time())
            self.log_data[IMU_IDX.ACCEL_X] = accel[0]
            self.log_data[IMU_IDX.ACCEL_Y] = accel[1]
            self.log_data[IMU_IDX.ACCEL_Z] = accel[2]
            self.log_data[IMU_IDX.MAGNETOMETER_X] = mag[0]
            self.log_data[IMU_IDX.MAGNETOMETER_Y] = mag[1]
            self.log_data[IMU_IDX.MAGNETOMETER_Z] = mag[2]
            self.log_data[IMU_IDX.GYROSCOPE_X] = gyro[0]
            self.log_data[IMU_IDX.GYROSCOPE_Y] = gyro[1]
            self.log_data[IMU_IDX.GYROSCOPE_Z] = gyro[2]

            DH.log_data("imu", self.log_data)

            self.log_print_counter += 1
            if self.log_print_counter % 10 == 0:
                # self.log_info(f"{dict(zip(self.data_keys, self.log_data))}")
                self.log_print_counter = 0
                self.log_info(f"accel: {self.log_data[IMU_IDX.ACCEL_X:IMU_IDX.ACCEL_Z]}")
                self.log_info(f"mag: {self.log_data[IMU_IDX.MAGNETOMETER_X:IMU_IDX.MAGNETOMETER_Z]}")
                self.log_info(f"gyro: {self.log_data[IMU_IDX.GYROSCOPE_X:IMU_IDX.GYROSCOPE_Z]}")
                # self.log_info(f"(mag, gyro): {self.log_data[IMU_IDX.MAGNETOMETER_X:IMU_IDX.GYROSCOPE_Z]}")
