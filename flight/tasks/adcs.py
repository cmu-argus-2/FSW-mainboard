# Attitude Determination and Control (ADC) task

import time

from apps.adcs.ad import TRIAD
from apps.adcs.igrf import igrf_eci
from apps.adcs.sun import (
    SUN_VECTOR_STATUS,
    approx_sun_position_ECI,
    compute_body_sun_vector_from_lux,
    in_eclipse,
    read_light_sensors,
)
from apps.telemetry.constants import ADCS_IDX
from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STATES
from ulab import numpy as np


class Task(TemplateTask):

    name = "ADCS"
    ID = 0x11

    data_keys = [
        "time",
        "ADCS_STATE",
        "GYRO_X",
        "GYRO_Y",
        "GYRO_Z",
        "MAG_X",
        "MAG_Y",
        "MAG_Z",
        "SUN_STATUS",
        "SUN_VEC_X",
        "SUN_VEC_Y",
        "SUN_VEC_Z",
        "ECLIPSE",
        "LIGHT_SENSOR_XP",
        "LIGHT_SENSOR_XM",
        "LIGHT_SENSOR_YP",
        "LIGHT_SENSOR_YM",
        "LIGHT_SENSOR_ZP1",
        "LIGHT_SENSOR_ZP2",
        "LIGHT_SENSOR_ZP3",
        "LIGHT_SENSOR_ZP4",
        "LIGHT_SENSOR_ZM",
        "XP_COIL_STATUS",
        "XM_COIL_STATUS",
        "YP_COIL_STATUS",
        "YM_COIL_STATUS",
        "ZP_COIL_STATUS",
        "ZM_COIL_STATUS",
        "COARSE_ATTITUDE_QW",  # Will see later if ok to reduce to short int (fixed point 2 bytes)
        "COARSE_ATTITUDE_QX",
        "COARSE_ATTITUDE_QY",
        "COARSE_ATTITUDE_QZ",
        "STAR_TRACKER_STATUS",
        "STAR_TRACKER_ATTITUDE_QW",  # will keep the 4 bytes precision
        "STAR_TRACKER_ATTITUDE_QX",
        "STAR_TRACKER_ATTITUDE_QY",
        "STAR_TRACKER_ATTITUDE_QZ",
    ]

    log_data = [0] * 37
    data_format = "LB" + 6 * "f" + "B" + 3 * "f" + "B" + 9 * "l" + 6 * "B" + 4 * "f" + "B" + 4 * "f"

    # Sun Acquisition
    THRESHOLD_ILLUMINATION_LUX = 3000
    sun_status = SUN_VECTOR_STATUS.NO_READINGS
    sun_vector = np.zeros(3)
    eclipse_state = False

    # Magnetic Control

    # Attitude Determination

    async def main_task(self):

        if SM.current_state == STATES.NOMINAL:

            if not DH.data_process_exists("adcs"):
                DH.register_data_process("adcs", self.data_keys, self.data_format, True, line_limit=100)

            # Log IMU data
            self.log_data[ADCS_IDX.TIME] = int(time.time())
            self.log_data[ADCS_IDX.MAG_X] = DH.get_latest_data("imu")[ADCS_IDX.MAG_X]
            self.log_data[ADCS_IDX.MAG_Y] = DH.get_latest_data("imu")[ADCS_IDX.MAG_Y]
            self.log_data[ADCS_IDX.MAG_Z] = DH.get_latest_data("imu")[ADCS_IDX.MAG_Z]
            self.log_data[ADCS_IDX.GYRO_X] = DH.get_latest_data("imu")[ADCS_IDX.GYRO_X]
            self.log_data[ADCS_IDX.GYRO_Y] = DH.get_latest_data("imu")[ADCS_IDX.GYRO_Y]
            self.log_data[ADCS_IDX.GYRO_Z] = DH.get_latest_data("imu")[ADCS_IDX.GYRO_Z]

            ## Sun Acquisition

            #  Must return the array directly
            lux_readings = read_light_sensors()
            self.sun_status, self.sun_vector = compute_body_sun_vector_from_lux(lux_readings)
            self.eclipse_state = in_eclipse(
                lux_readings,
                threshold_lux_illumination=self.THRESHOLD_ILLUMINATION_LUX,
            )

            self.log_data[ADCS_IDX.SUN_STATUS] = self.sun_status
            self.log_data[ADCS_IDX.SUN_VEC_X] = self.sun_vector[0]
            self.log_data[ADCS_IDX.SUN_VEC_Y] = self.sun_vector[1]
            self.log_data[ADCS_IDX.SUN_VEC_Z] = self.sun_vector[2]
            self.log_data[ADCS_IDX.ECLIPSE] = self.eclipse_state
            self.log_data[ADCS_IDX.LIGHT_SENSOR_XP] = lux_readings[0]
            self.log_data[ADCS_IDX.LIGHT_SENSOR_XM] = lux_readings[1]
            self.log_data[ADCS_IDX.LIGHT_SENSOR_YP] = lux_readings[2]
            self.log_data[ADCS_IDX.LIGHT_SENSOR_YM] = lux_readings[3]
            self.log_data[ADCS_IDX.LIGHT_SENSOR_ZM] = lux_readings[4]
            # Pyramid TBD

            ## Magnetic Control

            # TODO

            ## Attitude Determination

            # TODO

            # Data logging
            DH.log_data("adcs", self.log_data)
            self.log_info(f"{dict(zip(self.data_keys[8:11], self.log_data[8:11]))}")
