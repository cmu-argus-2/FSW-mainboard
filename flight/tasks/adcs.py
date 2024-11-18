# Attitude Determination and Control (ADC) task

import time

from apps.adcs.ad import TRIAD
from apps.adcs.frames import ecef_to_eci
from apps.adcs.igrf import igrf_eci
from apps.adcs.mcm import ControllerHandler, MagneticCoilAllocator
from apps.adcs.sun import (
    SUN_VECTOR_STATUS,
    approx_sun_position_ECI,
    compute_body_sun_vector_from_lux,
    in_eclipse,
    read_light_sensors,
)
from apps.telemetry.constants import ADCS_IDX, GPS_IDX, IMU_IDX
from core import DataHandler as DH
from core import TemplateTask
from core import state_manager as SM
from core.states import STATES
from ulab import numpy as np


class Task(TemplateTask):

    """data_keys = [
        "TIME_ADCS",
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
    ]"""

    time = int(time.time())

    log_data = [0] * 37
    # For now - keep the floats, will optimize the telemetry packet afterwards

    # Sun Acquisition
    THRESHOLD_ILLUMINATION_LUX = 3000
    sun_status = SUN_VECTOR_STATUS.NO_READINGS
    sun_vector = np.zeros(3)
    eclipse_state = False

    # Attitude Determination
    coarse_attitude = np.zeros(4)

    def __init__(self, id):
        super().__init__(id)
        self.name = "ADCS"  # Override the name

    async def main_task(self):

        if SM.current_state == STATES.NOMINAL:

            if not DH.data_process_exists("adcs"):
                data_format = "LB" + 6 * "f" + "B" + 3 * "f" + "B" + 9 * "H" + 6 * "B" + 4 * "f" + "B" + 4 * "f"
                DH.register_data_process("adcs", data_format, True, data_limit=100000, write_interval=5)

            self.time = int(time.time())

            # Log IMU data
            self.log_data[ADCS_IDX.TIME_ADCS] = self.time
            imu_mag_data = DH.get_latest_data("imu")[IMU_IDX.MAGNETOMETER_X : IMU_IDX.MAGNETOMETER_Z + 1]
            self.log_data[ADCS_IDX.MAG_X : ADCS_IDX.MAG_Z + 1] = imu_mag_data
            self.log_data[ADCS_IDX.GYRO_X : ADCS_IDX.GYRO_Z + 1] = DH.get_latest_data("imu")[
                IMU_IDX.GYROSCOPE_X : IMU_IDX.GYROSCOPE_Z + 1
            ]

            ## Sun Acquisition

            #  Must return the array directly
            lux_readings = read_light_sensors()  # lux
            self.sun_status, self.sun_vector = compute_body_sun_vector_from_lux(lux_readings)  # use full lux for sun vector
            self.eclipse_state = in_eclipse(
                lux_readings,
                threshold_lux_illumination=self.THRESHOLD_ILLUMINATION_LUX,
            )

            self.log_data[ADCS_IDX.SUN_STATUS] = self.sun_status
            self.log_data[ADCS_IDX.SUN_VEC_X] = self.sun_vector[0]
            self.log_data[ADCS_IDX.SUN_VEC_Y] = self.sun_vector[1]
            self.log_data[ADCS_IDX.SUN_VEC_Z] = self.sun_vector[2]
            self.log_data[ADCS_IDX.ECLIPSE] = self.eclipse_state
            # Log dlux (decilux) instead of lux for TM space efficiency
            self.log_data[ADCS_IDX.LIGHT_SENSOR_XP] = int(lux_readings[0] / 10)
            self.log_data[ADCS_IDX.LIGHT_SENSOR_XM] = int(lux_readings[1] / 10)
            self.log_data[ADCS_IDX.LIGHT_SENSOR_YP] = int(lux_readings[2] / 10)
            self.log_data[ADCS_IDX.LIGHT_SENSOR_YM] = int(lux_readings[3] / 10)
            self.log_data[ADCS_IDX.LIGHT_SENSOR_ZM] = int(lux_readings[4] / 10)
            # Pyramid TBD

            # see apps/adcs/mcm.py

            ## Magnetic Control
            # TODO state machine handling for control modes
            """
            dipole_moment_cmd = ControllerHandler.get_dipole_moment_command(
                sun_vector, magnetic_field, angular_velocity)
            MagneticCoilAllocator.set_voltages(dipole_moment_cmd)
            """

            ## Attitude Determination

            if DH.data_process_exists("gps"):
                # TODO GPS flag for valid position
                # Might need an attitude status flag
                R_ecef_to_eci = ecef_to_eci(self.time)
                gps_pos_ecef_meters = (
                    np.array(DH.get_latest_data("gps")[GPS_IDX.GPS_ECEF_X : GPS_IDX.GPS_ECEF_Z + 1]).reshape((3,)) * 0.01
                )
                gps_pos_eci_meters = np.dot(R_ecef_to_eci, gps_pos_ecef_meters)
                mag_eci = igrf_eci(self.time, gps_pos_eci_meters / 1000)
                sun_eci = approx_sun_position_ECI(self.time)

                # TRIAD
                self.coarse_attitude = TRIAD(sun_eci, mag_eci, self.sun_vector, imu_mag_data)
                self.log_data[ADCS_IDX.COARSE_ATTITUDE_QW] = (
                    self.coarse_attitude[0] if not is_nan(self.coarse_attitude[0]) else 0
                )
                self.log_data[ADCS_IDX.COARSE_ATTITUDE_QX] = (
                    self.coarse_attitude[1] if not is_nan(self.coarse_attitude[1]) else 0
                )
                self.log_data[ADCS_IDX.COARSE_ATTITUDE_QY] = (
                    self.coarse_attitude[2] if not is_nan(self.coarse_attitude[2]) else 0
                )
                self.log_data[ADCS_IDX.COARSE_ATTITUDE_QZ] = (
                    self.coarse_attitude[3] if not is_nan(self.coarse_attitude[3]) else 0
                )

            # Data logging
            DH.log_data("adcs", self.log_data)
            # self.log_info(f"{dict(zip(self.data_keys[8:13], self.log_data[8:13]))}")  # Sun
            # self.log_info(f"{dict(zip(self.data_keys[28:32], self.log_data[28:32]))}")  # Coarse attitude
            self.log_info(f"Sun: {self.log_data[8:13]}")
            self.log_info(f"Coarse attitude: {self.log_data[28:32]}")


def is_nan(x):
    # np.nan is not equal to itself
    return x != x
