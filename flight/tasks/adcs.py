# Attitude Determination and Control (ADC) task

import apps.adcs.sensors as sensors
from apps.adcs.acs import (
    bcross_controller,
    bdot_controller,
    mcm_coil_allocator,
    spin_stabilizing_controller,
    sun_pointing_controller,
    zero_all_coils,
)
from apps.adcs.consts import ControllerConst, ControllerModes, Modes, StatusConst
from apps.adcs.modemanager import update_mode
from apps.telemetry.constants import ADCS_IDX, CDH_IDX, class_length
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
_IDX_LENGTH = class_length(ADCS_IDX)


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
    ]"""

    log_data = [0] * _IDX_LENGTH
    coil_status = [0] * 6

    ## ADCS Modes and switching logic
    MODE = Modes.TUMBLING

    CONTROLLER_MODE = ControllerModes.BDOT  # BCROSS # SUN_POINTING  #

    # Sensor Data storage
    gyro_status = StatusConst.OK
    gyro_data = np.zeros((3,))

    mag_status = StatusConst.OK
    mag_data = np.zeros((3,))

    # for bdot controller
    prev_mag_data = np.zeros((3,))
    bdot_dt = 0.2  # time step for bdot controller, in seconds

    sun_status = StatusConst.OK
    sun_pos_body = np.zeros((3,))
    sun_lux = np.zeros((9,))

    coils_off = True
    last_mag_time = 0.0
    last_mtq_time = 0.0

    xp_deployed = False
    ym_deployed = False

    ctr_const = ControllerConst()

    def __init__(self, id):
        super().__init__(id)
        self.name = "ADCS"  # Override the name

    async def main_task(self):
        if SM.current_state == STATES.STARTUP:
            # check for deployment to update inertia matrix
            pass
        else:
            if not DH.data_process_exists("adcs"):
                data_format = "LBB" + 6 * "f" + "B" + 3 * "f" + 9 * "H" + 6 * "B"  # + 4 * "f"
                DH.register_data_process("adcs", data_format, True, data_limit=100000, write_interval=5)

            self.time = TPM.time()
            self.log_data[ADCS_IDX.TIME_ADCS] = self.time

            if not self.xp_deployed:
                xp_dist = sensors.read_deployment_sensors("XP")
                self.xp_deployed = xp_dist < 0 or xp_dist > 10
                if self.xp_deployed:
                    self.ctr_const.update_inertia_no_deploy(xp_deployed=self.xp_deployed, ym_deployed=self.ym_deployed)
            if not self.ym_deployed:
                ym_dist = sensors.read_deployment_sensors("YM")
                self.ym_deployed = ym_dist < 0 or ym_dist > 10
                if self.ym_deployed:
                    self.ctr_const.update_inertia_no_deploy(xp_deployed=self.xp_deployed, ym_deployed=self.ym_deployed)

            # ------------------------------------------------------------------------------------------------------------------------------------
            # DETUMBLING
            # ------------------------------------------------------------------------------------------------------------------------------------
            if SM.current_state == STATES.DETUMBLING:
                # Set bmx160 to max scale of 2000 deg/s
                if sensors.get_gyro_scale != 0:
                    sensors.set_gyro_scale(0)

                # Query the Gyro
                self.gyro_status, self.gyro_data = sensors.read_gyro()

                # Flags on whether to run coils or collect from magnetometer
                collect_mag, allow_coils = self.alternate_coil_and_mag()

                # Query Magnetometer
                if collect_mag:
                    self.prev_mag_data = self.mag_data.copy()
                    self.mag_status, self.mag_data = sensors.read_magnetometer()
                    new_last_mag_time = TPM.monotonic_float()
                    self.bdot_dt = new_last_mag_time - self.last_mag_time
                    self.last_mag_time = new_last_mag_time

                # Run Attitude Control
                if allow_coils:
                    self.attitude_control()
                    if self.coils_off:
                        self.coils_off = False
                    # self.last_mtb_time = TPM.time()
                    self.last_mtq_time = TPM.monotonic_float()
                else:
                    self.ensure_coils_off()

                # Check if detumbling has been completed
                self.MODE = update_mode(self.MODE, self.CONTROLLER_MODE, self.ctr_const)
                # if update_mode(self.MODE, self.ctr_const) != Modes.TUMBLING:
                #     self.ensure_coils_off()
                #     self.MODE = Modes.STABLE

            # ------------------------------------------------------------------------------------------------------------------------------------
            # LOW POWER or EXPERIMENT
            # ------------------------------------------------------------------------------------------------------------------------------------
            elif SM.current_state == STATES.LOW_POWER or SM.current_state == STATES.EXPERIMENT:
                # Turn coils off to conserve power
                self.ensure_coils_off()

            # ------------------------------------------------------------------------------------------------------------------------------------
            # NOMINAL
            # ------------------------------------------------------------------------------------------------------------------------------------
            else:
                if (
                    SM.current_state == STATES.NOMINAL
                    and not DH.get_latest_data("cdh")[CDH_IDX.DETUMBLING_ERROR_FLAG]
                    and update_mode(self.MODE, self.CONTROLLER_MODE, self.ctr_const) == Modes.TUMBLING
                ):
                    # Do not allow a switch to Detumbling from Low power
                    self.MODE = Modes.TUMBLING

                else:
                    # Set bmx160 scale to 125 deg/s, max resolution
                    if sensors.get_gyro_scale != 4:
                        sensors.set_gyro_scale(4)
                    # Query the Gyro
                    self.gyro_status, self.gyro_data = sensors.read_gyro()

                    # Flags on whether to run coils or collect from magnetometer
                    collect_mag, allow_coils = self.alternate_coil_and_mag()

                    # Query Magnetometer
                    if collect_mag:
                        self.prev_mag_data = self.mag_data.copy()
                        self.mag_status, self.mag_data = sensors.read_magnetometer()
                        new_last_mag_time = TPM.monotonic_float()
                        self.bdot_dt = new_last_mag_time - self.last_mag_time
                        self.last_mag_time = new_last_mag_time

                    # Query Sun Position
                    self.sun_status, self.sun_pos_body, self.sun_lux = sensors.read_sun_position()

                    # Identify Mode based on current sensor readings
                    new_mode = update_mode(self.MODE, self.CONTROLLER_MODE, self.ctr_const)
                    if new_mode != self.MODE:
                        self.ensure_coils_off()
                        self.MODE = new_mode

                    # Run attitude control if not in Low-power
                    if SM.current_state != STATES.LOW_POWER and self.MODE != Modes.ACS_OFF and allow_coils:
                        self.attitude_control()
                        # self.last_mtb_time = TPM.time()
                        if self.coils_off:
                            self.coils_off = False
                        self.last_mtq_time = TPM.monotonic_float()
                    else:
                        self.ensure_coils_off()

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
        mtq_throttle = np.zeros((3,))

        if self.CONTROLLER_MODE == ControllerModes.BDOT:
            if self.MODE != Modes.ACS_OFF:
                if not (self.mag_status != StatusConst.OK):
                    mtq_throttle = bdot_controller(self.mag_data, self.prev_mag_data, self.bdot_dt)

        elif self.CONTROLLER_MODE == ControllerModes.BCROSS:
            if self.MODE != Modes.ACS_OFF:
                if not (self.gyro_status != StatusConst.OK or self.mag_status != StatusConst.OK):
                    mtq_throttle = bcross_controller(self.mag_data, self.gyro_data)
        elif self.CONTROLLER_MODE == ControllerModes.SUN_POINTING:
            # Decide which controller to choose
            if self.MODE in [Modes.TUMBLING, Modes.STABLE]:  # spin-stabilizing controller

                if not (self.gyro_status != StatusConst.OK or self.mag_status != StatusConst.OK):
                    # Control MCMs and obtain coil statuses
                    mtq_throttle = spin_stabilizing_controller(self.gyro_data, self.mag_data, self.ctr_const)

            elif self.MODE == Modes.SUN_POINTING:  # Sun-pointed controller

                # Perform ACS iff a sun vector measurement is valid
                # i.e., ignore eclipses, insufficient readings etc.
                if not (
                    self.gyro_status != StatusConst.OK
                    or self.mag_status != StatusConst.OK
                    or self.sun_status != StatusConst.OK
                ):
                    mtq_throttle = sun_pointing_controller(
                        self.sun_pos_body, self.gyro_data, self.mag_data, self.ctr_const.INERTIA_MAT
                    )
            # Else, if in ACS_OFF, do not control MCMs
            # Commanded dipole moment stays zero

        self.coil_status = mcm_coil_allocator(mtq_throttle, self.mag_data)

    def alternate_coil_and_mag(self):
        """
        To preserve the quality of magnetometer readings, alternate between collecting from
        the magnetometer and running the coils.
         - If the magnetometer data was collected within the last 0.8 seconds, run the coils.
         If not, turn the coils off to settle their current/magnetic dipole before collecting data from the magnetometer again.
         - if the coils have been turned off for longer than 0.2 s (settling time), collect from the magnetometer
        """
        collect_mag = True
        run_coils = True
        # If the magnetometer data was collected within the last 0.8 seconds,
        # run the coils. If not, turn the coils off to settle their
        # current/magnetic dipole before collecting data from the magnetometer again.
        if TPM.monotonic_float() - self.last_mag_time <= 0.8:
            collect_mag = False
            run_coils = True
        else:
            collect_mag = False
            run_coils = False

        # if the coils have been turned off for longer than 0.2 s (settling time),
        # collect from the magnetometer
        if self.coils_off and (TPM.monotonic_float() - self.last_mtq_time > 0.2):
            collect_mag = True
        return collect_mag, run_coils

    def ensure_coils_off(self):
        """
        If the coils are not off, turn them off and update the last_mtq_time to prevent immediate reactivation.
        """
        if not self.coils_off:
            zero_all_coils()
            self.coils_off = True
            self.last_mtq_time = TPM.monotonic_float()

    # ------------------------------------------------------------------------------------------------------------------------------------
    """ LOGGING """

    # ------------------------------------------------------------------------------------------------------------------------------------
    def log(self):
        """
        Logs data to Data Handler
        Takes light sensor readings as input since they are not stored in AD
        """
        self.log_data[ADCS_IDX.MODE] = int(self.MODE)
        self.log_data[ADCS_IDX.CTRL_MODE] = int(self.CONTROLLER_MODE)
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
        self.log_info(f"Controller Mode : {self.CONTROLLER_MODE}")
        self.log_info(f"Gyro Ang Vel : {self.gyro_data}")
        # [TODO:] Remove later
        self.log_info(f"Mag Field : {self.log_data[ADCS_IDX.MAG_X:ADCS_IDX.MAG_Z + 1]}")
        self.log_info(f"Sun Vector : {self.log_data[ADCS_IDX.SUN_VEC_X:ADCS_IDX.SUN_VEC_Z + 1]}")
        self.log_info(f"Sun Status : {self.log_data[ADCS_IDX.SUN_STATUS]}")
        self.log_info(f"Gyro Status : {self.gyro_status}")
        self.log_info(f"Mag Status : {self.mag_status}")
