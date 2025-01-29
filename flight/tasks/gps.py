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

            if SM.current_state == STATES.STARTUP:
                pass

            else:
                if not DH.data_process_exists("gps"):
                    # TODO : This format is no longer correct
                    data_format = "LBBBHIiiiiHHHHHiiiiii"
                    DH.register_data_process("gps", data_format, True, data_limit=100000, write_interval=10)

                print("Trying to run SATELLITE.GPS.update()")
                SATELLITE.GPS.update()

                # Assuming we have a fix for now
                if SATELLITE.GPS.has_fix():

                    print("GPS has fix is True")

                    # TODO GPS frame parsing - get ECEF in (cm) and ECEF velocity in cm/s
                    # TODO : Change the time to get the GPS time rather than the system time here

                    self.log_data[GPS_IDX.TIME_GPS] = int(time.time())
                    print("Time type: ", type(self.log_data[GPS_IDX.TIME_GPS]))
                    self.log_data[GPS_IDX.GPS_MESSAGE_ID] = SATELLITE.GPS.message_id
                    print("Message ID type: ", type(self.log_data[GPS_IDX.GPS_MESSAGE_ID]))
                    self.log_data[GPS_IDX.GPS_FIX_MODE] = SATELLITE.GPS.fix_mode
                    print("Fix Mode type: ", type(self.log_data[GPS_IDX.GPS_FIX_MODE]))
                    self.log_data[GPS_IDX.GPS_NUMBER_OF_SV] = SATELLITE.GPS.number_of_sv
                    print("Number of SV type: ", type(self.log_data[GPS_IDX.GPS_NUMBER_OF_SV]))
                    self.log_data[GPS_IDX.GPS_GNSS_WEEK] = SATELLITE.GPS.week
                    print("GPS Week type: ", type(self.log_data[GPS_IDX.GPS_GNSS_WEEK]))
                    self.log_data[GPS_IDX.GPS_GNSS_TOW] = SATELLITE.GPS.tow
                    print("GPS TOW type: ", type(self.log_data[GPS_IDX.GPS_GNSS_TOW]))
                    self.log_data[GPS_IDX.GPS_LATITUDE] = SATELLITE.GPS.latitude
                    print("GPS Latitude type: ", type(self.log_data[GPS_IDX.GPS_LATITUDE]))
                    self.log_data[GPS_IDX.GPS_LONGITUDE] = SATELLITE.GPS.longitude
                    print("GPS Longitude type: ", type(self.log_data[GPS_IDX.GPS_LONGITUDE]))
                    self.log_data[GPS_IDX.GPS_ELLIPSOID_ALT] = SATELLITE.GPS.ellipsoid_altitude
                    print("GPS Ellipsoid type: ", type(self.log_data[GPS_IDX.GPS_ELLIPSOID_ALT]))
                    self.log_data[GPS_IDX.GPS_MEAN_SEA_LVL_ALT] = SATELLITE.GPS.mean_sea_level_altitude
                    print("GPS MSL type: ", type(self.log_data[GPS_IDX.GPS_MEAN_SEA_LVL_ALT]))
                    self.log_data[GPS_IDX.GPS_GDOP] = SATELLITE.GPS.gdop
                    print("GDOP type: ", type(self.log_data[GPS_IDX.GPS_GDOP]))
                    self.log_data[GPS_IDX.GPS_PDOP] = SATELLITE.GPS.pdop
                    print("PDOP type: ", type(self.log_data[GPS_IDX.GPS_PDOP]))
                    self.log_data[GPS_IDX.GPS_HDOP] = SATELLITE.GPS.hdop
                    print("HDOP type: ", type(self.log_data[GPS_IDX.GPS_HDOP]))
                    self.log_data[GPS_IDX.GPS_VDOP] = SATELLITE.GPS.vdop
                    print("VDOP type: ", type(self.log_data[GPS_IDX.GPS_VDOP]))
                    self.log_data[GPS_IDX.GPS_TDOP] = SATELLITE.GPS.tdop
                    print("TDOP type: ", type(self.log_data[GPS_IDX.GPS_TDOP]))
                    self.log_data[GPS_IDX.GPS_ECEF_X] = SATELLITE.GPS.ecef_x  # cm
                    print("GPS ECEF X type: ", type(self.log_data[GPS_IDX.GPS_ECEF_X]))
                    self.log_data[GPS_IDX.GPS_ECEF_Y] = SATELLITE.GPS.ecef_y
                    print("GPS ECEF Y type: ", type(self.log_data[GPS_IDX.GPS_ECEF_Y]))
                    self.log_data[GPS_IDX.GPS_ECEF_Z] = SATELLITE.GPS.ecef_z
                    print("GPS ECEF Z type: ", type(self.log_data[GPS_IDX.GPS_ECEF_Z]))
                    self.log_data[GPS_IDX.GPS_ECEF_VX] = SATELLITE.GPS.ecef_vx  # cm/s
                    print("GPS ECEF VX type: ", type(self.log_data[GPS_IDX.GPS_ECEF_VX]))
                    self.log_data[GPS_IDX.GPS_ECEF_VY] = SATELLITE.GPS.ecef_vy
                    print("GPS ECEF VY type: ", type(self.log_data[GPS_IDX.GPS_ECEF_VY]))
                    self.log_data[GPS_IDX.GPS_ECEF_VZ] = SATELLITE.GPS.ecef_vz
                    print("GPS ECEF VZ type: ", type(self.log_data[GPS_IDX.GPS_ECEF_VZ]))

                    DH.log_data("gps", self.log_data)

                    print("GPS Data has been logged!")
            # self.log_info(f"{dict(zip(self.data_keys[-6:], self.log_data[-6:]))}")
            self.log_info(f"GPS ECEF: {self.log_data[GPS_IDX.GPS_ECEF_X:]}")
