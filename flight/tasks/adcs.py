# Attitude Determination and Control (ADC) task

import time

from apps.adcs.ad import AttitudeDetermination
from apps.adcs.consts import ModeConst  # , MCMConst, PhysicalConst
from apps.adcs.modes import Modes
from apps.telemetry.constants import ADCS_IDX, CDH_IDX
from core import DataHandler as DH
from core import TemplateTask
from core import state_manager as SM
from core.states import STATES
from ulab import numpy as np

"""
    ASSUMPTIONS :
        - ADCS Task runs at 5 Hz (TBD if we can't handle this)
        - In detumbling, control loop executes every 200ms
        - In nominal/experiment, for 4 executions, we do nothing. On the fifth, we run full MEKF + control
"""


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

    log_data = [0] * 31

    ## ADCS Modes and switching logic
    MODE = Modes.TUMBLING

    # Sub-task architecture
    execution_counter = 0

    def __init__(self, id):
        super().__init__(id)
        self.name = "ADCS"  # Override the name

        # Attitude Determination
        self.AD = AttitudeDetermination(id, self.name)  # Logs everything from AD within ADCS Task ID

    async def main_task(self):
        if SM.current_state == STATES.STARTUP:
            pass

        else:

            if not DH.data_process_exists("adcs"):
                data_format = "LB" + 6 * "f" + "B" + 3 * "f" + 9 * "H" + 6 * "B" + 4 * "f"
                DH.register_data_process("adcs", data_format, True, data_limit=100000, write_interval=5)

            self.time = int(time.time())
            self.log_data[ADCS_IDX.TIME_ADCS] = self.time

            # ------------------------------------------------------------------------------------------------------------------------------------
            # DETUMBLING
            # ------------------------------------------------------------------------------------------------------------------------------------
            if SM.current_state == STATES.DETUMBLING:

                # Query the Gyro
                self.AD.gyro_update(self.time, update_covariance=False)

                # Query Magnetometer
                self.AD.magnetometer_update(self.time, update_covariance=False)

                # Run Attitude Control
                self.attitude_control()

                # Check if detumbling has been completed
                if np.linalg.norm(self.AD.state[self.AD.omega_idx]) <= ModeConst.STABLE_TOL:
                    self.MODE = Modes.STABLE

            # ------------------------------------------------------------------------------------------------------------------------------------
            # LOW POWER
            # ------------------------------------------------------------------------------------------------------------------------------------
            elif SM.current_state == STATES.LOW_POWER:

                if not self.AD.initialized:
                    self.AD.initialize_mekf()

                else:

                    if self.execution_counter < 4:
                        # Update Gyro and attitude estimate via propagation
                        self.AD.gyro_update(self.time, update_covariance=False)
                        self.execution_counter += 1

                    else:
                        # Update Each sensor with covariances
                        self.AD.position_update(self.time)
                        self.AD.sun_position_update(self.time, update_covariance=True)
                        self.AD.gyro_update(self.time, update_covariance=True)
                        self.AD.magnetometer_update(self.time, update_covariance=True)

                        # No Attitude Control in Low-power mode

                        # Reset Execution counter
                        self.execution_counter = 0

            # ------------------------------------------------------------------------------------------------------------------------------------
            # NOMINAL & EXPERIMENT
            # ------------------------------------------------------------------------------------------------------------------------------------
            else:

                if not self.AD.initialized:
                    self.AD.initialize_mekf()

                elif (
                    SM.current_state == STATES.NOMINAL
                    and np.linalg.norm(self.AD.state[self.AD.omega_idx]) > ModeConst.EKF_INIT_TOL
                    and not DH.get_latest_data("cdh")[CDH_IDX.DETUMBLING_ERROR_FLAG]
                ):
                    self.MODE = Modes.TUMBLING

                else:
                    if self.execution_counter == 0:
                        # TODO : Turn coils off before measurements to allow time for coils to settle
                        pass

                    if self.execution_counter < 4:
                        # Update Gyro and attitude estimate via propagation
                        self.AD.gyro_update(self.time, update_covariance=False)
                        self.execution_counter += 1

                    else:
                        # Update Each sensor with covariances
                        self.AD.position_update(self.time)
                        self.AD.sun_position_update(self.time, update_covariance=True)
                        self.AD.gyro_update(self.time, update_covariance=True)
                        self.AD.magnetometer_update(self.time, update_covariance=True)

                        # Run attitude control
                        self.attitude_control()

                        # Reset Execution counter
                        self.execution_counter = 0

            # Log data
            # NOTE: In detumbling, most of the log will be zeros since very few sensors are queried
            self.log()

    # ------------------------------------------------------------------------------------------------------------------------------------
    """ Attitude Control Auxiliary Functions """
    # ------------------------------------------------------------------------------------------------------------------------------------
    def attitude_control(self):
        """
        Performs attitude control on the spacecraft
        """
        pass

    # ------------------------------------------------------------------------------------------------------------------------------------
    """ LOGGING """
    # ------------------------------------------------------------------------------------------------------------------------------------
    def log(self):
        """
        Logs data to Data Handler
        Takes light sensor readings as input since they are not stored in AD
        """
        self.log_data[ADCS_IDX.MODE] = int(self.MODE)
        self.log_data[ADCS_IDX.GYRO_X] = self.AD.state[10]
        self.log_data[ADCS_IDX.GYRO_Y] = self.AD.state[11]
        self.log_data[ADCS_IDX.GYRO_Z] = self.AD.state[12]
        self.log_data[ADCS_IDX.MAG_X] = self.AD.state[16]
        self.log_data[ADCS_IDX.MAG_Y] = self.AD.state[17]
        self.log_data[ADCS_IDX.MAG_Z] = self.AD.state[18]
        self.log_data[ADCS_IDX.SUN_STATUS] = int(self.AD.state[22])
        self.log_data[ADCS_IDX.SUN_VEC_X] = self.AD.state[19]
        self.log_data[ADCS_IDX.SUN_VEC_Y] = self.AD.state[20]
        self.log_data[ADCS_IDX.SUN_VEC_Z] = self.AD.state[21]
        self.log_data[ADCS_IDX.LIGHT_SENSOR_XM] = int(self.AD.state[23]) & 0xFFFF
        self.log_data[ADCS_IDX.LIGHT_SENSOR_XP] = int(self.AD.state[24]) & 0xFFFF
        self.log_data[ADCS_IDX.LIGHT_SENSOR_YM] = int(self.AD.state[25]) & 0xFFFF
        self.log_data[ADCS_IDX.LIGHT_SENSOR_YP] = int(self.AD.state[26]) & 0xFFFF
        self.log_data[ADCS_IDX.LIGHT_SENSOR_ZM] = int(self.AD.state[27]) & 0xFFFF
        # self.log_data[ADCS_IDX.LIGHT_SENSOR_ZP1] = self.AD.state[28]
        # self.log_data[ADCS_IDX.LIGHT_SENSOR_ZP2] = self.AD.state[29]
        # self.log_data[ADCS_IDX.LIGHT_SENSOR_ZP3] = self.AD.state[30]
        # self.log_data[ADCS_IDX.LIGHT_SENSOR_ZP4] = self.AD.state[31]
        # TODO : extract and add coil status
        self.log_data[ADCS_IDX.ATTITUDE_QW] = self.AD.state[6]
        self.log_data[ADCS_IDX.ATTITUDE_QX] = self.AD.state[7]
        self.log_data[ADCS_IDX.ATTITUDE_QY] = self.AD.state[8]
        self.log_data[ADCS_IDX.ATTITUDE_QZ] = self.AD.state[9]
        DH.log_data("adcs", self.log_data)
        if self.execution_counter == 0:
            self.log_info(f"Gyro Ang Vel : {self.log_data[ADCS_IDX.GYRO_X:ADCS_IDX.GYRO_Z+1]}")
