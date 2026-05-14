# GPS Task

from core import DataHandler as DH
from core import TemplateTask
from core import state_manager as SM
from core.dh_constants import GPS_IDX
from core.states import STATES
from core.time_processor import TimeProcessor as TPM
from hal.configuration import SATELLITE
from micropython import const

"""
    Fix Modes in GPS Message:
    For the S1216F8-GL Flight Module, the value of the fix mode is as follows in the AN0030 protocol:
    Quality of fix of S1216F8-GL:
        00: NO_FIX,
        01: FIX_PREDICTION
        02: FIX_2D
        03: FIX_3D
        04: FIX_DIFFERENTIAL

    For the PX1120S Module, the value is as follows in the AN0037 protocol:
    Quality of fix of PX1120:
        0: no fix
        1: 2D
        2: 3D
        3: 3D+DGNSS

    NOTE: For the PX1120S, _FIX_MODE_THR should be set to 2 for replicate the same fix_mode as S1216F8-GL
"""

_FIX_MODE_THR = const(3)  # 3D Fix with S1216F8-GL


class Task(TemplateTask):
    """data_keys = [
        "TIME",
        "GPS_MESSAGE_ID",
        "GPS_FIX_MODE",
        "GPS_GNSS_WEEK",
        "GPS_GNSS_TOW",
        "GPS_GDOP",
        "GPS_PDOP",
        "GPS_HDOP",
        "GPS_VDOP",
        "GPS_TDOP",
        "GPS_ECEF_X",
        "GPS_ECEF_Y",
        "GPS_ECEF_Z",
        "GPS_ECEF_VX",
        "GPS_ECEF_VY",
        "GPS_ECEF_VZ",
    ]"""

    log_data = [0] * 18

    def __init__(self, id):
        super().__init__(id)
        self.name = "GPS"

    async def main_task(self):
        if SM.current_state == STATES.STARTUP:
            pass

        else:
            if SATELLITE.GPS_AVAILABLE:
                if not DH.data_process_exists("gps"):
                    data_format = "LBBIBHIHHHHHllllll"

                    # data limit is around 100minutes. No need to make it smaller for downlink 
                    DH.register_data_process("gps", data_format, True, data_limit=10000, write_interval=1)

                # Check if the module sent a valid nav data message
                if SATELLITE.GPS.update():
                    # Check if the fix is at least a 2D fix (fix_mode >= 2)
                    if SATELLITE.GPS.has_fix():
                        self.log_data[GPS_IDX.TIME_GPS] = int(SATELLITE.GPS.unix_time)
                        self.log_data[GPS_IDX.GPS_MESSAGE_ID] = int(SATELLITE.GPS.message_id)
                        self.log_data[GPS_IDX.GPS_FIX_MODE] = int(SATELLITE.GPS.fix_mode)
                        self.log_data[GPS_IDX.GPS_LAST_FIX_TIME] = int(SATELLITE.GPS.unix_time)
                        self.log_data[GPS_IDX.GPS_LAST_FIX_MODE] = int(SATELLITE.GPS.fix_mode)
                        self.log_data[GPS_IDX.GPS_GNSS_WEEK] = int(SATELLITE.GPS.week)
                        self.log_data[GPS_IDX.GPS_GNSS_TOW] = int(SATELLITE.GPS.tow)
                        self.log_data[GPS_IDX.GPS_GDOP] = int(SATELLITE.GPS.gdop)
                        self.log_data[GPS_IDX.GPS_PDOP] = int(SATELLITE.GPS.pdop)
                        self.log_data[GPS_IDX.GPS_HDOP] = int(SATELLITE.GPS.hdop)
                        self.log_data[GPS_IDX.GPS_VDOP] = int(SATELLITE.GPS.vdop)
                        self.log_data[GPS_IDX.GPS_TDOP] = int(SATELLITE.GPS.tdop)
                        self.log_data[GPS_IDX.GPS_ECEF_X] = int(SATELLITE.GPS.ecef_x)
                        self.log_data[GPS_IDX.GPS_ECEF_Y] = int(SATELLITE.GPS.ecef_y)
                        self.log_data[GPS_IDX.GPS_ECEF_Z] = int(SATELLITE.GPS.ecef_z)
                        self.log_data[GPS_IDX.GPS_ECEF_VX] = int(SATELLITE.GPS.ecef_vx)
                        self.log_data[GPS_IDX.GPS_ECEF_VY] = int(SATELLITE.GPS.ecef_vy)
                        self.log_data[GPS_IDX.GPS_ECEF_VZ] = int(SATELLITE.GPS.ecef_vz)

                        # Log the current sample after log_data has been updated.
                        self.log_info("GPS module got a valid fix")
                        self.log_info(f"GPS ECEF: {self.log_data[GPS_IDX.GPS_ECEF_X:]}")

                        DH.log_data("gps", self.log_data)

                        # If RTC is inactive, set the TPM time reference regardless of fix quality
                        if SATELLITE.RTC_AVAILABLE is False:
                            TPM.set_time_reference(SATELLITE.GPS.unix_time)

                        # Only update RTC time if the fix is better than _FIX_MODE_THR
                        elif SATELLITE.GPS.fix_mode >= _FIX_MODE_THR:
                            TPM.set_time(SATELLITE.GPS.unix_time)

                    else:
                        self.log_info("GPS module did not get a valid fix")

                    # Log info
                    self.log_info(f"GPS Time: {self.log_data[GPS_IDX.TIME_GPS]}")
                    self.log_info(f"GPS Fix Mode: {self.log_data[GPS_IDX.GPS_FIX_MODE]}")

                else:
                    # Did not get a valid nav data message
                    reason = SATELLITE.GPS.last_update_status
                    if reason is None:
                        reason = "GPS module did not send a valid nav data message"
                    self.log_info(reason)

            else:
                # GPS is not active in HAL
                self.log_warning("GPS module is no longer active on the SC")
