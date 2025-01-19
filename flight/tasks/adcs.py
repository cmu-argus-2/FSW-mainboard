# Attitude Determination and Control (ADC) task

import time

from apps.adcs.ad import TRIAD
from apps.adcs.consts import ModeConst  # , MCMConst, PhysicalConst
from apps.adcs.frames import ecef_to_eci
from apps.adcs.igrf import igrf_eci

"""from apps.adcs.mcm import (
    ControllerHandler,
    MagneticCoilAllocator,
    get_spin_stabilizing_dipole_moment,
    get_sun_pointing_dipole_moment,
)"""
from apps.adcs.modes import Modes
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
from hal.configuration import SATELLITE
from ulab import numpy as np


class Task(TemplateTask):
    """data_keys = [
        "TIME_ADCS",
        "MODE",
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
        "COARSE_ATTITUDE_QW",
        "COARSE_ATTITUDE_QX",
        "COARSE_ATTITUDE_QY",
        "COARSE_ATTITUDE_QZ",
    ]"""

    ## ADCS Modes
    MODE = Modes.TUMBLING

    log_data = [0] * 37

    # Sun Acquisition
    sun_status = SUN_VECTOR_STATUS.NO_READINGS
    sun_vector = np.zeros(3)
    eclipse_state = False

    # Attitude Determination
    coarse_attitude = np.zeros(4)

    def __init__(self, id):
        super().__init__(id)
        self.name = "ADCS"  # Override the name

    async def main_task(self):

        if SM.current_state == STATES.STARTUP:
            pass

        else:

            ## Attitude Determination

            if not DH.data_process_exists("adcs"):
                data_format = "LB" + 6 * "f" + "B" + 3 * "f" + "B" + 9 * "H" + 6 * "B" + 4 * "f" + "B" + 4 * "f"
                DH.register_data_process("adcs", data_format, True, data_limit=100000, write_interval=5)

            self.time = int(time.time())
            self.log_data[ADCS_IDX.TIME_ADCS] = self.time

            # Log IMU data
            if SATELLITE.IMU_AVAILABLE:
                imu_mag_data = DH.get_latest_data("imu")[IMU_IDX.MAGNETOMETER_X : IMU_IDX.MAGNETOMETER_Z + 1]
                self.log_data[ADCS_IDX.MAG_X : ADCS_IDX.MAG_Z + 1] = imu_mag_data
                imu_ang_vel = DH.get_latest_data("imu")[IMU_IDX.GYROSCOPE_X : IMU_IDX.GYROSCOPE_Z + 1]
                self.log_data[ADCS_IDX.GYRO_X : ADCS_IDX.GYRO_Z + 1] = imu_ang_vel

            ## Sun Acquisition
            lux_readings = read_light_sensors()  # lux
            self.sun_status, self.sun_vector = compute_body_sun_vector_from_lux(lux_readings)  # use full lux for sun vector
            self.eclipse_state = in_eclipse(lux_readings)

            self.log_data[ADCS_IDX.SUN_STATUS] = self.sun_status
            self.log_data[ADCS_IDX.SUN_VEC_X] = self.sun_vector[0]
            self.log_data[ADCS_IDX.SUN_VEC_Y] = self.sun_vector[1]
            self.log_data[ADCS_IDX.SUN_VEC_Z] = self.sun_vector[2]
            self.log_data[ADCS_IDX.ECLIPSE] = self.eclipse_state
            # Log dlux (decilux) instead of lux for TM space efficiency
            self.log_data[ADCS_IDX.LIGHT_SENSOR_XP] = int(lux_readings[0] * 0.1)
            self.log_data[ADCS_IDX.LIGHT_SENSOR_XM] = int(lux_readings[1] * 0.1)
            self.log_data[ADCS_IDX.LIGHT_SENSOR_YP] = int(lux_readings[2] * 0.1)
            self.log_data[ADCS_IDX.LIGHT_SENSOR_YM] = int(lux_readings[3] * 0.1)
            self.log_data[ADCS_IDX.LIGHT_SENSOR_ZM] = int(lux_readings[4] * 0.1)
            # Pyramid TBD

            if DH.data_process_exists("gps") and SATELLITE.GPS_AVAILABLE:  # Must be replaced by orbit processor module
                # TODO GPS flag for valid position

                R_ecef_to_eci = ecef_to_eci(self.time)
                gps_pos_ecef_meters = (
                    np.array(DH.get_latest_data("gps")[GPS_IDX.GPS_ECEF_X : GPS_IDX.GPS_ECEF_Z + 1]).reshape((3,)) * 0.01
                )
                gps_pos_eci_meters = np.dot(R_ecef_to_eci, gps_pos_ecef_meters)
                mag_eci = igrf_eci(self.time, gps_pos_eci_meters / 1000)
                sun_eci = approx_sun_position_ECI(self.time)

                # TRIAD
                if SATELLITE.IMU_AVAILABLE:
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
            self.log_info(f"Sun: {self.log_data[8:13]}")
            self.log_info(f"Coarse attitude: {self.log_data[28:32]}")

            ## Attitude Control

            # need to account for if gyro / sun vector unavailable
            if self.eclipse_state:
                sun_vector_err = ModeConst.SUN_POINTED_TOL
            else:
                sun_vector_err = ModeConst.SUN_VECTOR_REF - self.sun_vector

            if np.linalg.norm(imu_ang_vel) >= ModeConst.STABLE_TOL:
                self.MODE = Modes.TUMBLING
            elif np.linalg.norm(sun_vector_err) >= ModeConst.SUN_POINTED_TOL:
                self.MODE = Modes.STABLE
            else:
                self.MODE = Modes.SUN_POINTED

            self.log_data[ADCS_IDX.MODE] = self.MODE

            # TODO: Fix attitude control stack for Circuitpython + hardware testing
            """
            scaled_ang_vel = imu_ang_vel / ControllerHandler.ang_vel_target
            spin_err = ControllerHandler.spin_axis - scaled_ang_vel
            pointing_err = self.sun_vector - scaled_ang_vel
            """

            """ang_momentum = PhysicalConst.INERTIA_MAT @ imu_ang_vel
            scaled_momentum = ang_momentum / ControllerHandler.momentum_target
            spin_err = ControllerHandler.spin_axis - scaled_momentum
            pointing_err = self.sun_vector - scaled_momentum

            if not np.linalg.norm(spin_err) < MCMConst.SPIN_ERROR_TOL:
                dipole_moment = get_spin_stabilizing_dipole_moment(
                    imu_mag_data,
                    spin_err,
                )
            elif not self.eclipse_state and not np.linalg.norm(sun_vector_err) < MCMConst.POINTING_ERROR_TOL:
                dipole_moment = get_sun_pointing_dipole_moment(
                    imu_mag_data,
                    pointing_err,
                )
            else:
                dipole_moment = np.zeros(3)
            MagneticCoilAllocator.set_voltages(dipole_moment)"""


def is_nan(x):
    # np.nan is not equal to itself
    return x != x
