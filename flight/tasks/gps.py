# GPS Task

import time

from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STATES


class Task(TemplateTask):

    name = "GPS"
    ID = 0x0B

    data_keys = [
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
    ]

    async def main_task(self):

        if SM.current_state == STATES.STARTUP:
            pass
        elif SM.current_state == STATES.NOMINAL:
            if not DH.data_process_exists("gps"):
                DH.register_data_process("gps", self.data_keys, "fBBBHIiiiiHHHHHiiiiii", True, line_limit=200)
            pass

        # TODO GPS readings

        readings = {
            "TIME": time.time(),
            "GPS_MESSAGE_ID": 0,
            "GPS_FIX_MODE": 0,
            "GPS_NUMBER_OF_SV": 0,
            "GPS_GNSS_WEEK": 0,
            "GPS_GNSS_TOW": 0,
            "GPS_LATITUDE": 0.0,
            "GPS_LONGITUDE": 0.0,
            "GPS_ELLIPSOID_ALT": 0.0,
            "GPS_MEAN_SEA_LVL_ALT": 0.0,
            "GPS_GDOP": 0.0,
            "GPS_PDOP": 0.0,
            "GPS_HDOP": 0.0,
            "GPS_VDOP": 0.0,
            "GPS_TDOP": 0.0,
            "GPS_ECEF_X": 0.0,
            "GPS_ECEF_Y": 0.0,
            "GPS_ECEF_Z": 0.0,
            "GPS_ECEF_VX": 0.0,
            "GPS_ECEF_VY": 0.0,
            "GPS_ECEF_VZ": 0.0,
        }

        DH.log_data("gps", readings)
        print(f"[{self.ID}][{self.name}] ...")
