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

# from apps.adcs.modemanager import update_mode
from core import DataHandler as DH
from core import TemplateTask
from core import state_manager as SM
from core.dh_constants import ADCS_IDX, class_length
from core.satellite_config import adcs_config as CONFIG
from core.states import STATES
from core.time_processor import TimeProcessor as TPM
from ulab import numpy as np

_IDX_LENGTH = class_length(ADCS_IDX)
_ADCS_DATA_FORMAT = "LBBffffffBfffHHHHHHHHHBBBBBB"


class Task(TemplateTask):
    """data_keys = [
        "TIME_ADCS",
        "MODE",
        "CONTROLLER_MODE",
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
        "LIGHT_SENSOR_ZP_XP",
        "LIGHT_SENSOR_ZP_YM",
        "LIGHT_SENSOR_ZP_XM",
        "LIGHT_SENSOR_ZP_YP",
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

    CONTROLLER_MODE = CONFIG.CONTROLLER_MODE  # BCROSS # SUN_POINTING  #

    # Sensor Data storage
    gyro_status = StatusConst.OK
    gyro_data = np.zeros((3,))

    mag_status = StatusConst.OK
    mag_data = np.zeros((3,))

    sun_status = StatusConst.OK
    sun_pos_body = np.zeros((3,))
    sun_lux = np.zeros((9,))

    coils_off = True

    _MAG_SAMPLE_DT = 0.08
    _MAG_N_SAMPLES = 6
    _BDOT_COIL_ON_TIME = 0.5

    def __init__(self, id):
        super().__init__(id)
        self.name = "ADCS"  # Override the name

    async def main_task(self):
        if SM.current_state == STATES.STARTUP:
            # check for deployment to update inertia matrix
            pass
        else:
            if not DH.data_process_exists("adcs"):
                DH.register_data_process("adcs", _ADCS_DATA_FORMAT, True, data_limit=100000, write_interval=2)

            ControllerModes.load()

            # Check for controller mode update from commands
            if self.CONTROLLER_MODE != ControllerModes.current_mode:
                self.CONTROLLER_MODE = ControllerModes.current_mode

            self.log_data[ADCS_IDX.TIME_ADCS] = TPM.time()

            self.mag_status, self.mag_data = sensors.read_magnetometer()
            self.gyro_status, self.gyro_data = sensors.read_gyro()
            self.sun_status, self.sun_pos_body, self.sun_lux = sensors.read_sun_position()

            self.log()

            if SM.current_state == STATES.LOW_POWER or SM.current_state == STATES.EXPERIMENT:
                # In low power or experiment mode, we want to conserve power by turning off the coils and not running the control cycle
                self.ensure_coils_off()
            else:
                if SM.current_state == STATES.DETUMBLING:
                    # Set bmx160 to max scale of 2000 deg/s
                    sensors.set_gyro_scale(0)
                elif SM.current_state == STATES.NOMINAL:
                    # Set bmx160 scale to 125 deg/s, max resolution
                    sensors.set_gyro_scale(4)

                self.MODE = sensors.update_mode(
                    self.MODE, self.CONTROLLER_MODE, self.gyro_status, self.gyro_data, self.sun_status, self.sun_pos_body
                )

                if self.CONTROLLER_MODE == ControllerModes.BDOT:
                    self._bdot_cycle()
                else:
                    self._bcross_sun_cycle(1.0)

    # --- Attitude Control ---
    def _apply_control(self):
        if self.MODE == Modes.ACS_OFF:
            self.ensure_coils_off()
            return
        mtq_throttle = ControllerConst.FALLBACK_CONTROL
        if self.CONTROLLER_MODE == ControllerModes.BCROSS:
            if not (self.gyro_status != StatusConst.OK or self.mag_status != StatusConst.OK):
                mtq_throttle = bcross_controller(self.mag_data, self.gyro_data)
        elif self.CONTROLLER_MODE == ControllerModes.SUN_POINTING:
            if self.MODE == Modes.TUMBLING or self.MODE == Modes.STABLE:
                if not (self.gyro_status != StatusConst.OK or self.mag_status != StatusConst.OK):
                    mtq_throttle = spin_stabilizing_controller(self.gyro_data, self.mag_data)
            elif self.MODE == Modes.SUN_POINTING:
                if not (
                    self.gyro_status != StatusConst.OK
                    or self.mag_status != StatusConst.OK
                    or self.sun_status != StatusConst.OK
                ):
                    mtq_throttle = sun_pointing_controller(self.sun_pos_body, self.gyro_data, self.mag_data)
        self.coil_status = mcm_coil_allocator(mtq_throttle, self.mag_data)
        self.coils_off = False

    def _bdot_cycle(self):
        """
        B-dot control cycle: sample 6 mag readings, run coils, coils off.
        Total duration: 5 x 0.08 + 0.5 = 0.9 s.
        """
        if self.MODE == Modes.ACS_OFF:
            self.ensure_coils_off()
            return
        self._mag_buffer = []
        for k in range(self._MAG_N_SAMPLES):
            status, reading = sensors.read_magnetometer()
            if status == StatusConst.OK:
                self._mag_buffer.append(reading)
            if k < self._MAG_N_SAMPLES - 1:
                TPM.sleep(self._MAG_SAMPLE_DT)

        if self._mag_buffer:
            self.mag_data = self._mag_buffer[-1]
            self.mag_status = StatusConst.OK
        else:
            self.mag_status = StatusConst.MAG_FAIL

        if len(self._mag_buffer) == self._MAG_N_SAMPLES:
            buf = np.array(self._mag_buffer)
            throttle = bdot_controller(buf, self._MAG_SAMPLE_DT)
            self.coil_status = mcm_coil_allocator(throttle, self.mag_data)
            self.coils_off = False
        else:
            self.ensure_coils_off()

        TPM.sleep(self._BDOT_COIL_ON_TIME)
        self.ensure_coils_off()

    def _bcross_sun_cycle(self, duration):
        """
        B-cross / Sun-pointing control cycle:
          1. Update ADCS mode based on snapshot readings
          2. Every 50 ms for duration seconds:
             read gyro and update the control law / coils
             (future: propagate sun and mag vectors with gyro)
          3. Coils off at the end
        """
        GYRO_INTERVAL = 0.05  # 50 ms
        t_start = TPM.monotonic_float()

        while TPM.monotonic_float() - t_start < duration:
            loop_start = TPM.monotonic_float()

            self.gyro_status, self.gyro_data = sensors.read_gyro()
            # TODO: Propagate sun vector and magnetometer with gyro reading
            self._apply_control()

            elapsed = TPM.monotonic_float() - loop_start
            remaining = GYRO_INTERVAL - elapsed
            if remaining > 0:
                TPM.sleep(remaining)

        self.ensure_coils_off()

    def ensure_coils_off(self):
        """
        If the coils are not off, turn them off.
        """
        if not self.coils_off:
            zero_all_coils()
            self.coils_off = True

    # --- Logging ---
    def log(self):
        """
        Logs data to Data Handler
        Takes light sensor readings as input since they are not stored in AD
        """
        self.log_data[ADCS_IDX.MODE] = int(self.MODE)
        self.log_data[ADCS_IDX.CONTROLLER_MODE] = int(self.CONTROLLER_MODE)
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
        self.log_data[ADCS_IDX.LIGHT_SENSOR_ZP_XP] = int(self.sun_lux[5]) & 0xFFFF
        self.log_data[ADCS_IDX.LIGHT_SENSOR_ZP_YM] = int(self.sun_lux[6]) & 0xFFFF
        self.log_data[ADCS_IDX.LIGHT_SENSOR_ZP_XM] = int(self.sun_lux[7]) & 0xFFFF
        self.log_data[ADCS_IDX.LIGHT_SENSOR_ZP_YP] = int(self.sun_lux[8]) & 0xFFFF
        self.log_data[ADCS_IDX.XP_COIL_STATUS] = int(self.coil_status[0])
        self.log_data[ADCS_IDX.XM_COIL_STATUS] = int(self.coil_status[1])
        self.log_data[ADCS_IDX.YP_COIL_STATUS] = int(self.coil_status[2])
        self.log_data[ADCS_IDX.YM_COIL_STATUS] = int(self.coil_status[3])
        self.log_data[ADCS_IDX.ZP_COIL_STATUS] = int(self.coil_status[4])
        self.log_data[ADCS_IDX.ZM_COIL_STATUS] = int(self.coil_status[5])
        DH.log_data("adcs", self.log_data)

        # Log Gyro Angular Velocities
        self.log_debug(f"Time :  {TPM.monotonic_float()}")  # self.time}")
        self.log_debug(f"ADCS Mode : {self.MODE}")
        self.log_debug(f"Controller Mode : {self.CONTROLLER_MODE}")
        self.log_debug(f"Gyro Ang Vel : {self.log_data[ADCS_IDX.GYRO_X:ADCS_IDX.GYRO_Z + 1]}")
        self.log_debug(f"Mag Field : {self.log_data[ADCS_IDX.MAG_X:ADCS_IDX.MAG_Z + 1]}")
        self.log_debug(f"Sun Vector : {self.log_data[ADCS_IDX.SUN_VEC_X:ADCS_IDX.SUN_VEC_Z + 1]}")
        self.log_debug(f"Sun Status : {self.log_data[ADCS_IDX.SUN_STATUS]}")
        self.log_debug(f"Gyro Status : {self.gyro_status}")
        self.log_debug(f"Mag Status : {self.mag_status}")
