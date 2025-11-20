# Attitude Determination and Control (ADC) task

import apps.adcs.sensors as sensors
from apps.adcs.acs import mcm_coil_allocator, spin_stabilizing_controller, sun_pointing_controller, zero_all_coils
from apps.adcs.consts import Modes, StatusConst
from apps.telemetry.constants import ADCS_IDX, CDH_IDX
from core import DataHandler as DH
from core import TemplateTask
from core import state_manager as SM
from core.states import STATES
from core.time_processor import TimeProcessor as TPM
from ulab import numpy as np

"""
    ASSUMPTIONS :
        - ADCS Task runs at 5 Hz (TBD if we can't handle this)
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
        "LIGHT_SENSOR_ZP_1",
        "LIGHT_SENSOR_ZP_2",
        "LIGHT_SENSOR_ZP_3",
        "LIGHT_SENSOR_ZP_4",
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
    coil_status = [0] * 6

    ## ADCS Modes and switching logic
    MODE = Modes.TUMBLING

    # Sensor Data storage
    gyro_status = StatusConst.OK
    gyro_data = np.zeros((3,))

    mag_status = StatusConst.OK
    mag_data = np.zeros((3,))

    sun_status = StatusConst.OK
    sun_pos_body = np.zeros((3,))
    sun_lux = np.zeros((9,))

    mag_counter = 0

    def __init__(self, id):
        super().__init__(id)
        self.name = "ADCS"  # Override the name

    async def main_task(self):
        if SM.current_state == STATES.STARTUP:
            pass

        else:
            if not DH.data_process_exists("adcs"):
                data_format = "LB" + 6 * "f" + "B" + 3 * "f" + 9 * "H" + 6 * "B" + 4 * "f"
                DH.register_data_process("adcs", data_format, True, data_limit=100000, write_interval=5)

            self.time = TPM.time()
            self.log_data[ADCS_IDX.TIME_ADCS] = self.time

            # ------------------------------------------------------------------------------------------------------------------------------------
            # DETUMBLING
            # ------------------------------------------------------------------------------------------------------------------------------------
            if SM.current_state == STATES.DETUMBLING:
                # Query the Gyro
                self.gyro_status, self.gyro_data = sensors.read_gyro()

                # Query Magnetometer
                if self.mag_counter == 0:
                    self.mag_status, self.mag_data = sensors.read_magnetometer()
                    self.last_mag_time = TPM.time()

                # Run Attitude Control
                if self.mag_counter < 3:
                    self.attitude_control()
                    self.last_mtb_time = TPM.time()
                else:
                    zero_all_coils()

                self.mag_counter += 1
                if self.mag_counter == 5:
                    self.mag_counter = 0
                # Check if detumbling has been completed
                if sensors.current_mode(self.MODE) != Modes.TUMBLING:
                    zero_all_coils()
                    self.MODE = Modes.STABLE

            # ------------------------------------------------------------------------------------------------------------------------------------
            # LOW POWER or EXPERIMENT
            # ------------------------------------------------------------------------------------------------------------------------------------
            elif SM.current_state == STATES.LOW_POWER or SM.current_state == STATES.EXPERIMENT:
                # Turn coils off to conserve power
                zero_all_coils()
                self.mag_counter = 0

            # ------------------------------------------------------------------------------------------------------------------------------------
            # NOMINAL
            # ------------------------------------------------------------------------------------------------------------------------------------
            else:
                if (
                    SM.current_state == STATES.NOMINAL
                    and not DH.get_latest_data("cdh")[CDH_IDX.DETUMBLING_ERROR_FLAG]
                    and sensors.current_mode(self.MODE) == Modes.TUMBLING
                ):
                    # Do not allow a switch to Detumbling from Low power
                    self.MODE = Modes.TUMBLING

                else:
                    # Query the Gyro
                    self.gyro_status, self.gyro_data = sensors.read_gyro()

                    # Query Magnetometer
                    if self.mag_counter == 0:
                        self.mag_status, self.mag_data = sensors.read_magnetometer()
                        self.last_mag_time = TPM.time()

                    # Query Sun Position
                    self.sun_status, self.sun_pos_body, self.sun_lux = sensors.read_sun_position()

                    # identify Mode based on current sensor readings
                    new_mode = sensors.current_mode(self.MODE)
                    if new_mode != self.MODE:
                        zero_all_coils()
                        self.MODE = new_mode

                    # Run attitude control if not in Low-power
                    if SM.current_state != STATES.LOW_POWER and self.MODE != Modes.ACS_OFF and self.mag_counter < 3:
                        self.attitude_control()
                        self.last_mtb_time = TPM.time()
                    else:
                        zero_all_coils()

                    self.mag_counter += 1
                    if self.mag_counter == 5:
                        self.mag_counter = 0

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

        # Decide which controller to choose
        if self.MODE in [Modes.TUMBLING, Modes.STABLE]:  # B-cross controller

            if self.gyro_status != StatusConst.OK or self.mag_status != StatusConst.OK:
                return

            # Control MCMs and obtain coil statuses
            dipole_moment = spin_stabilizing_controller(self.gyro_data, self.mag_data)

        elif self.MODE == Modes.SUN_POINTED:  # Sun-pointed controller

            # Perform ACS iff a sun vector measurement is valid
            # i.e., ignore eclipses, insufficient readings etc.
            if self.gyro_status != StatusConst.OK or self.mag_status != StatusConst.OK or self.sun_status != StatusConst.OK:
                return

            # Control MCMs and obtain coil statuses
            dipole_moment = sun_pointing_controller(self.sun_pos_body, self.gyro_data, self.mag_data)
        else:
            # If in ACS_OFF or any other mode, do not control MCMs
            # Just zero out the dipole moment
            dipole_moment = np.zeros((3,))

        self.coil_status = mcm_coil_allocator(dipole_moment)

    # ------------------------------------------------------------------------------------------------------------------------------------
    """ LOGGING """

    # ------------------------------------------------------------------------------------------------------------------------------------
    def log(self):
        """
        Logs data to Data Handler
        Takes light sensor readings as input since they are not stored in AD
        """
        self.log_data[ADCS_IDX.MODE] = int(self.MODE)
        self.log_data[ADCS_IDX.GYRO_X] = self.gyro_data[0]
        self.log_data[ADCS_IDX.GYRO_Y] = self.gyro_data[1]
        self.log_data[ADCS_IDX.GYRO_Z] = self.gyro_data[2]
        self.log_data[ADCS_IDX.MAG_X] = self.mag_data[0]
        self.log_data[ADCS_IDX.MAG_Y] = self.mag_data[1]
        self.log_data[ADCS_IDX.MAG_Z] = self.mag_data[2]
        self.log_data[ADCS_IDX.SUN_STATUS] = int(self.sun_status)
        self.log_data[ADCS_IDX.SUN_VEC_X] = self.sun_pos_body[0]
        self.log_data[ADCS_IDX.SUN_VEC_Y] = self.sun_pos_body[1]
        self.log_data[ADCS_IDX.SUN_VEC_Z] = self.sun_pos_body[2]
        self.log_data[ADCS_IDX.LIGHT_SENSOR_XM] = int(self.sun_lux[0]) & 0xFFFF
        self.log_data[ADCS_IDX.LIGHT_SENSOR_XP] = int(self.sun_lux[1]) & 0xFFFF
        self.log_data[ADCS_IDX.LIGHT_SENSOR_YM] = int(self.sun_lux[2]) & 0xFFFF
        self.log_data[ADCS_IDX.LIGHT_SENSOR_YP] = int(self.sun_lux[3]) & 0xFFFF
        self.log_data[ADCS_IDX.LIGHT_SENSOR_ZM] = int(self.sun_lux[4]) & 0xFFFF
        self.log_data[ADCS_IDX.LIGHT_SENSOR_ZP1] = int(self.sun_lux[5]) & 0xFFFF
        self.log_data[ADCS_IDX.LIGHT_SENSOR_ZP2] = int(self.sun_lux[6]) & 0xFFFF
        self.log_data[ADCS_IDX.LIGHT_SENSOR_ZP3] = int(self.sun_lux[7]) & 0xFFFF
        self.log_data[ADCS_IDX.LIGHT_SENSOR_ZP4] = int(self.sun_lux[8]) & 0xFFFF
        self.log_data[ADCS_IDX.XP_COIL_STATUS] = int(self.coil_status[0])
        self.log_data[ADCS_IDX.XM_COIL_STATUS] = int(self.coil_status[1])
        self.log_data[ADCS_IDX.YP_COIL_STATUS] = int(self.coil_status[2])
        self.log_data[ADCS_IDX.YM_COIL_STATUS] = int(self.coil_status[3])
        self.log_data[ADCS_IDX.ZP_COIL_STATUS] = int(self.coil_status[4])
        self.log_data[ADCS_IDX.ZM_COIL_STATUS] = int(self.coil_status[5])
        DH.log_data("adcs", self.log_data)

        # Log Gyro Angular Velocities
        self.log_info(f"ADCS Mode : {self.MODE}")
        self.log_info(f"Gyro Ang Vel : {self.gyro_data}")
        # [TODO:] Remove later
        self.log_info(f"Mag Field : {self.log_data[ADCS_IDX.MAG_X:ADCS_IDX.MAG_Z + 1]}")
        self.log_info(f"Sun Vector : {self.log_data[ADCS_IDX.SUN_VEC_X:ADCS_IDX.SUN_VEC_Z + 1]}")
        self.log_info(f"Sun Status : {self.log_data[ADCS_IDX.SUN_STATUS]}")
        self.log_info(f"Gyro Status : {self.gyro_status}")
        self.log_info(f"Mag Status : {self.mag_status}")

        # from hal.configuration import SATELLITE
        # from ulab import numpy as np

        # SATELLITE.set_fsw_state(np.concatenate((self.AD.state[0:22], self.AD.true_map)))
