# Attitude Determination and Control (ADC) task

import time
from ulab import numpy as np

from core import TemplateTask
from core.states import STATES
from core import state_manager as SM
from core import DataHandler as DH
from hal.configuration import SATELLITE

from apps.adcs.ad import AttitudeDetermination
from apps.telemetry.constants import ADCS_IDX
from apps.adcs.modes import Modes
from apps.adcs.consts import ModeConst  # , MCMConst, PhysicalConst
"""
    ASSUMPTIONS : 
        - ADCS Task runs at 1 Hz 
        - Magnetometer settles within 400ms
        - Task breakdown by counter
        
        |<-gyro->|<-gyro->|<-gyro->|<-gyro->|<-Full EKF update->
        |<-gyro, MCM->|<-gyro, MCM->|<-gyro, MCM->|<-gyro, MCM->|<-gyro, MCM off->|
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

    log_data = [0] * 37
    
    ## ADCS Modes
    MODE = Modes.TUMBLING

    # Attitude Determination
    AD = AttitudeDetermination()

    def __init__(self, id):
        super().__init__(id)
        self.name = "ADCS"  # Override the name

    async def main_task(self):

        if SM.current_state == STATES.STARTUP:
            pass

        else:

            if not DH.data_process_exists("adcs"):
                data_format = "LB" + 6 * "f" + "B" + 3 * "f" + "B" + 9 * "H" + 6 * "B" + 4 * "f" + "B" + 4 * "f"
                DH.register_data_process("adcs", data_format, True, data_limit=100000, write_interval=5)

            self.time = int(time.time())
            self.log_data[ADCS_IDX.TIME_ADCS] = self.time
            
            if not self.AD.initialized:
                initialized = self.AD.initialize_mekf()
            
            else:
                
                for counter in range(10):
                    
                    # For the first 4 and last 5 steps, update the gyro alone
                    if counter < 4 or counter > 5:
                        gyro_status, gyro_sample_time, omega_body = self.AD.read_gyro()
                        self.AD.gyro_update(gyro_status, gyro_sample_time, omega_body) # No covariance update
                        
                    elif counter == 5:
                        
                        # Update position estimate
                        self.AD.position_update()
                        
                        # Update sun sensor estimates
                        sun_status, sun_pos_body, light_sensor_lux_readings = self.AD.read_sun_position()
                        self.AD.sun_position_update(sun_status, sun_pos_body)
                        
                        # Update magnetometer
                        mag_status, mag_query_time, mag_field_body = self.AD.read_magnetometer()
                        self.AD.magnetometer_update(mag_status, mag_field_body)
                        
                        # Update gyro
                        gyro_status, gyro_sample_time, omega_body = self.AD.read_gyro()
                        self.AD.gyro_update(gyro_status, gyro_sample_time, omega_body, update_error_covariance=True)
                        
                        # Run Controller
                        # ------------------------------------------------------------------------------------------------------------------------------------
                        """ ATTITUDE CONTROL """
                        # ------------------------------------------------------------------------------------------------------------------------------------
                        if SM.current_state != STATES.LOW_POWER: # No attitude control in Low-power
                            # TODO : Controller Logic
                            ## Attitude Control

                            # need to account for if gyro / sun vector unavailable
                            if self.eclipse_state:
                                sun_vector_err = ModeConst.SUN_POINTED_TOL
                            else:
                                sun_vector_err = ModeConst.SUN_VECTOR_REF - self.sun_vector

                            if np.linalg.norm(self.AD.state[7:10]) >= ModeConst.STABLE_TOL:
                                self.MODE = Modes.TUMBLING
                            elif np.linalg.norm(sun_vector_err) >= ModeConst.SUN_POINTED_TOL:
                                self.MODE = Modes.STABLE
                            else:
                                self.MODE = Modes.SUN_POINTED

                            self.log_data[ADCS_IDX.MODE] = self.MODE
                            self.log_info(f"Mode: {self.MODE}")
                        
                        # ------------------------------------------------------------------------------------------------------------------------------------
                        """ LOGGING """
                        # ------------------------------------------------------------------------------------------------------------------------------------
                        self.log_data[ADCS_IDX.TIME_ADCS] = gyro_sample_time
                        self.log_data[ADCS_IDX.MODE] = self.MODE
                        self.log_data[ADCS_IDX.GYRO_X] = self.AD.state[7]
                        self.log_data[ADCS_IDX.GYRO_Y] = self.AD.state[8]
                        self.log_data[ADCS_IDX.GYRO_Z] = self.AD.state[9]
                        self.log_data[ADCS_IDX.MAG_X] = self.AD.state[13]
                        self.log_data[ADCS_IDX.MAG_Y] = self.AD.state[14]
                        self.log_data[ADCS_IDX.MAG_Z] = self.AD.state[15]
                        self.log_data[ADCS_IDX.SUN_STATUS] = self.AD.state[19]
                        self.log_data[ADCS_IDX.SUN_VEC_X] = self.AD.state[16]
                        self.log_data[ADCS_IDX.SUN_VEC_Y] = self.AD.state[17]
                        self.log_data[ADCS_IDX.SUN_VEC_Z] = self.AD.state[18]
                        self.log_data[ADCS_IDX.LIGHT_SENSOR_XM] = light_sensor_lux_readings[0]
                        self.log_data[ADCS_IDX.LIGHT_SENSOR_XP] = light_sensor_lux_readings[1]
                        self.log_data[ADCS_IDX.LIGHT_SENSOR_YM] = light_sensor_lux_readings[2]
                        self.log_data[ADCS_IDX.LIGHT_SENSOR_YP] = light_sensor_lux_readings[3]
                        self.log_data[ADCS_IDX.LIGHT_SENSOR_ZM] = light_sensor_lux_readings[4]
                        self.log_data[ADCS_IDX.LIGHT_SENSOR_ZP1] = light_sensor_lux_readings[5]
                        self.log_data[ADCS_IDX.LIGHT_SENSOR_ZP2] = light_sensor_lux_readings[6]
                        self.log_data[ADCS_IDX.LIGHT_SENSOR_ZP3] = light_sensor_lux_readings[7]
                        self.log_data[ADCS_IDX.LIGHT_SENSOR_ZP4] = light_sensor_lux_readings[8]
                        # TODO : extract and add coil status
                        self.log_data[ADCS_IDX.COARSE_ATTITUDE_QW] = self.AD.state[3]
                        self.log_data[ADCS_IDX.COARSE_ATTITUDE_QX] = self.AD.state[4]
                        self.log_data[ADCS_IDX.COARSE_ATTITUDE_QY] = self.AD.state[5]
                        self.log_data[ADCS_IDX.COARSE_ATTITUDE_QZ] = self.AD.state[6]
                        
                        DH.log_data("adcs", self.log_data)
                        self.log_info(f"Sun: {self.log_data[8:13]}")
                        self.log_info(f"Coarse attitude: {self.log_data[28:32]}") 
                        
                    if counter == 9: # Special handling to turn MCM off
                        # TODO : Turn MCM Off
                        pass
                    
                        
                        
                
                
                
                    