# GPS Task

import time

from apps.telemetry.constants import GPS_IDX
from core import DataHandler as DH
from core import TemplateTask
from core import state_manager as SM
from core.states import STATES
from hal.configuration import SATELLITE


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

        if SATELLITE.GPS_AVAILABLE:

            if SM.current_state == STATES.NOMINAL:
                if not DH.data_process_exists("gps"):
                    data_format = "LBBBHIiiiiHHHHHiiiiii"
                    DH.register_data_process("gps", data_format, True, data_limit=100000, write_interval=10)

                SATELLITE.GPS.update()

                # Assuming we have a fix for now
                if SATELLITE.GPS.has_fix():

                    # TODO GPS frame parsing - get ECEF in (cm) and ECEF velocity in cm/s

                    self.log_data[GPS_IDX.TIME_GPS] = int(time.time())
                    self.log_data[GPS_IDX.GPS_MESSAGE_ID] = SATELLITE.GPS.parsed_nav_data["message_id"]
                    self.log_data[GPS_IDX.GPS_FIX_MODE] = SATELLITE.GPS.parsed_nav_data["fix_mode"]
                    self.log_data[GPS_IDX.GPS_NUMBER_OF_SV] = SATELLITE.GPS.parsed_nav_data["number_of_sv"]
                    self.log_data[GPS_IDX.GPS_GNSS_WEEK] = SATELLITE.GPS.parsed_nav_data["gps_week"]
                    self.log_data[GPS_IDX.GPS_GNSS_TOW] = SATELLITE.GPS.parsed_nav_data["tow"]
                    self.log_data[GPS_IDX.GPS_LATITUDE] = SATELLITE.GPS.parsed_nav_data["latitude"]
                    self.log_data[GPS_IDX.GPS_LONGITUDE] = SATELLITE.GPS.parsed_nav_data["longitude"]
                    self.log_data[GPS_IDX.GPS_ELLIPSOID_ALT] = SATELLITE.GPS.parsed_nav_data["ellipsoid_alt"]
                    self.log_data[GPS_IDX.GPS_MEAN_SEA_LVL_ALT] = SATELLITE.GPS.parsed_nav_data["mean_sea_lvl_alt"]
                    self.log_data[GPS_IDX.GPS_GDOP] = SATELLITE.GPS.parsed_nav_data["gdop"]
                    self.log_data[GPS_IDX.GPS_PDOP] = SATELLITE.GPS.parsed_nav_data["pdop"]
                    self.log_data[GPS_IDX.GPS_HDOP] = SATELLITE.GPS.parsed_nav_data["hdop"]
                    self.log_data[GPS_IDX.GPS_VDOP] = SATELLITE.GPS.parsed_nav_data["vdop"]
                    self.log_data[GPS_IDX.GPS_TDOP] = SATELLITE.GPS.parsed_nav_data["tdop"]
                    self.log_data[GPS_IDX.GPS_ECEF_X] = SATELLITE.GPS.parsed_nav_data["ecef_x"]  # cm
                    self.log_data[GPS_IDX.GPS_ECEF_Y] = SATELLITE.GPS.parsed_nav_data["ecef_y"]
                    self.log_data[GPS_IDX.GPS_ECEF_Z] = SATELLITE.GPS.parsed_nav_data["ecef_z"]
                    self.log_data[GPS_IDX.GPS_ECEF_VX] = SATELLITE.GPS.parsed_nav_data["ecef_vx"]  # cm/s
                    self.log_data[GPS_IDX.GPS_ECEF_VY] = SATELLITE.GPS.parsed_nav_data["ecef_vy"]
                    self.log_data[GPS_IDX.GPS_ECEF_VZ] = SATELLITE.GPS.parsed_nav_data["ecef_vz"]

                    DH.log_data("gps", self.log_data)
            # self.log_info(f"{dict(zip(self.data_keys[-6:], self.log_data[-6:]))}")
            self.log_info(f"GPS ECEF: {self.log_data[GPS_IDX.GPS_ECEF_X:]}")
