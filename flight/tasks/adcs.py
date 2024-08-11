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
        "COARSE_ATTITUDE_QW",
        "COARSE_ATTITUDE_QX",
        "COARSE_ATTITUDE_QY",
        "COARSE_ATTITUDE_QZ",
        "STAR_TRACKER_STATUS",
        "STAR_TRACKER_ATTITUDE_QW",
        "STAR_TRACKER_ATTITUDE_QX",
        "STAR_TRACKER_ATTITUDE_QY",
        "STAR_TRACKER_ATTITUDE_QZ",
    ]

    # Sun Acquisition
    THRESHOLD_ILLUMINATION_LUX = 3000
    sun_status = SUN_VECTOR_STATUS.NO_READINGS
    sun_vector = np.zeros(3)
    eclipse_state = False

    # Magnetic Control

    # Attitude Determination

    async def main_task(self):

        if SM.current_state == STATES.NOMINAL:

            ## Sun Acquisition

            #  Must return the array directly
            lux_readings = read_light_sensors()
            self.sun_status, self.sun_vector = compute_body_sun_vector_from_lux(lux_readings)
            self.eclipse_state = in_eclipse(
                lux_readings,
                threshold_lux_illumination=self.THRESHOLD_ILLUMINATION_LUX,
            )

            ## Magnetic Control

            # TODO

            ## Attitude Determination

            # TODO

        pass
