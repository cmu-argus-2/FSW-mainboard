# GPS Task

from apps.telemetry.constants import GPS_IDX
from core import DataHandler as DH
from core import TemplateTask
from core import state_manager as SM
from core.states import STATES
from core.time_processor import TimeProcessor as TPM
from hal.configuration import SATELLITE
from micropython import const

"""
    Fix Modes in GPS NMEA Message:

    0 - No fix: The GPS receiver has not obtained a valid fix or has lost the fix.
    1 - GPS fix: A 2D fix is available (latitude and longitude, but altitude is not necessarily reliable).
    2 - Differential GPS fix: A 2D fix is available, with differential corrections applied for improved accuracy.
    3 - 3D fix: A 3D fix is available (latitude, longitude, and altitude are all valid and reliable).
    4 - GNSS fix: A fix using signals from multiple GNSS systems (e.g., GPS, GLONASS, Galileo, BeiDou).
    5 - Time fix: A fix based on time synchronization, typically used in high-precision or timing applications.

    For updating the RTC's time reference, a fix mode of at least 3 should be used, to guarantee accurate time setting.
    The RTC does not have a very high drift over time, so unnecessary updates from bad GPS fixes should be avoided.

    However, if the RTC is inactive, the TPM time reference should be updated for any valid fix, since it will always be
    better than the TPM's best-effort timekeeping.
"""
_FIX_MODE_THR = const(3)


class Task(TemplateTask):
    """data_keys = [
        "TIME",
        "GPS_MESSAGE_ID",
        "GPS_FIX_MODE",
        "GPS_NUMBER_OF_SV",
        "GPS_GNSS_WEEK",
        "GPS_GNSS_TOW",  # Time of week
        "GPS_LATITUDE",
        "GPS_LONGITUDE",
        "GPS_ELLIPSOID_ALT",
        "GPS_MEAN_SEA_LVL_ALT",
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

    log_data = [0] * 21

    def __init__(self, id):
        super().__init__(id)
        self.name = "GPS"

    async def main_task(self):
        if SM.current_state == STATES.STARTUP:
            pass

        else:
            if SATELLITE.GPS_AVAILABLE:
                if not DH.data_process_exists("gps"):
                    data_format = "LBBBHLllllHHHHHllllll"
                    DH.register_data_process("gps", data_format, True, data_limit=100000, write_interval=1)

                # Check if the module sent a valid nav data message
                if SATELLITE.GPS.update():
                    # Check if the fix is at least a 2D fix (fix_mode >= 1)
                    if SATELLITE.GPS.has_fix():
                        # If a valid message and a fix, update GPS log info
                        self.log_info("GPS module got a valid fix")
                        self.log_info(f"GPS ECEF: {self.log_data[GPS_IDX.GPS_ECEF_X:]}")

                        self.log_data[GPS_IDX.TIME_GPS] = int(SATELLITE.GPS.unix_time)
                        self.log_data[GPS_IDX.GPS_MESSAGE_ID] = SATELLITE.GPS.message_id
                        self.log_data[GPS_IDX.GPS_FIX_MODE] = SATELLITE.GPS.fix_mode
                        self.log_data[GPS_IDX.GPS_NUMBER_OF_SV] = SATELLITE.GPS.number_of_sv
                        self.log_data[GPS_IDX.GPS_GNSS_WEEK] = SATELLITE.GPS.week
                        self.log_data[GPS_IDX.GPS_GNSS_TOW] = SATELLITE.GPS.tow
                        self.log_data[GPS_IDX.GPS_LATITUDE] = SATELLITE.GPS.latitude
                        self.log_data[GPS_IDX.GPS_LONGITUDE] = SATELLITE.GPS.longitude
                        self.log_data[GPS_IDX.GPS_ELLIPSOID_ALT] = SATELLITE.GPS.ellipsoid_altitude
                        self.log_data[GPS_IDX.GPS_MEAN_SEA_LVL_ALT] = SATELLITE.GPS.mean_sea_level_altitude
                        self.log_data[GPS_IDX.GPS_GDOP] = SATELLITE.GPS.gdop
                        self.log_data[GPS_IDX.GPS_PDOP] = SATELLITE.GPS.pdop
                        self.log_data[GPS_IDX.GPS_HDOP] = SATELLITE.GPS.hdop
                        self.log_data[GPS_IDX.GPS_VDOP] = SATELLITE.GPS.vdop
                        self.log_data[GPS_IDX.GPS_TDOP] = SATELLITE.GPS.tdop
                        self.log_data[GPS_IDX.GPS_ECEF_X] = SATELLITE.GPS.ecef_x  # cm
                        self.log_data[GPS_IDX.GPS_ECEF_Y] = SATELLITE.GPS.ecef_y
                        self.log_data[GPS_IDX.GPS_ECEF_Z] = SATELLITE.GPS.ecef_z
                        self.log_data[GPS_IDX.GPS_ECEF_VX] = SATELLITE.GPS.ecef_vx  # cm/s
                        self.log_data[GPS_IDX.GPS_ECEF_VY] = SATELLITE.GPS.ecef_vy
                        self.log_data[GPS_IDX.GPS_ECEF_VZ] = SATELLITE.GPS.ecef_vz

                        DH.log_data("gps", self.log_data)

                        # If RTC is inactive, set the TPM time reference regardless of fix quality
                        if SATELLITE.RTC_AVAILABLE is False:
                            TPM.set_time_reference(SATELLITE.GPS.unix_time)

                        # Only update RTC time if the fix is better than _FIX_MODE_THR
                        if SATELLITE.GPS.fix_mode > _FIX_MODE_THR:
                            TPM.set_time(SATELLITE.GPS.unix_time)

                    else:
                        self.log_info("GPS module did not get a valid fix")

                    # Log info
                    self.log_info(f"GPS Time: {self.log_data[GPS_IDX.TIME_GPS]}")
                    self.log_info(f"GPS Fix Mode: {self.log_data[GPS_IDX.GPS_FIX_MODE]}")
                    self.log_info(f"Number of SV: {self.log_data[GPS_IDX.GPS_NUMBER_OF_SV]}")

                else:
                    # Did not get a valid nav data message
                    self.log_info("GPS module did not send a valid nav data message")

            else:
                # GPS is not active in HAL
                self.log_warning("GPS module is no longer active on the SC")
