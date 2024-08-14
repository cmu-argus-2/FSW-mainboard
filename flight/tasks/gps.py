# GPS Task

import time

from apps.telemetry.constants import GPS_IDX
from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STATES


class Task(TemplateTask):

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

    data_format = "LBBBHIiiiiHHHHHiiiiii"
    log_data = [0] * 21

    async def main_task(self):

        if SM.current_state == STATES.STARTUP:
            pass
        elif SM.current_state == STATES.NOMINAL:
            if not DH.data_process_exists("gps"):
                DH.register_data_process("gps", self.data_keys, self.data_format, True, line_limit=200)

            # TODO GPS frame parsing - get ECEF in (cm) and ECEF velocity in cm/s

            self.log_data[GPS_IDX.TIME] = int(time.time())
            self.log_data[GPS_IDX.GPS_MESSAGE_ID] = 0
            self.log_data[GPS_IDX.GPS_FIX_MODE] = 0
            self.log_data[GPS_IDX.GPS_NUMBER_OF_SV] = 0
            self.log_data[GPS_IDX.GPS_GNSS_WEEK] = 0
            self.log_data[GPS_IDX.GPS_GNSS_TOW] = 0
            self.log_data[GPS_IDX.GPS_LATITUDE] = 0
            self.log_data[GPS_IDX.GPS_LONGITUDE] = 0
            self.log_data[GPS_IDX.GPS_ELLIPSOID_ALT] = 0
            self.log_data[GPS_IDX.GPS_MEAN_SEA_LVL_ALT] = 0
            self.log_data[GPS_IDX.GPS_GDOP] = 0
            self.log_data[GPS_IDX.GPS_PDOP] = 0
            self.log_data[GPS_IDX.GPS_HDOP] = 0
            self.log_data[GPS_IDX.GPS_VDOP] = 0
            self.log_data[GPS_IDX.GPS_TDOP] = 0
            self.log_data[GPS_IDX.GPS_ECEF_X] = 24161658  # cm
            self.log_data[GPS_IDX.GPS_ECEF_Y] = -64844741
            self.log_data[GPS_IDX.GPS_ECEF_Z] = 21809692
            self.log_data[GPS_IDX.GPS_ECEF_VX] = 66390526  # cm/s
            self.log_data[GPS_IDX.GPS_ECEF_VY] = 24738890
            self.log_data[GPS_IDX.GPS_ECEF_VZ] = -73684928

        DH.log_data("gps", self.log_data)
        self.log_info(f"{dict(zip(self.data_keys[-6:], self.log_data[-6:]))}")
