"""
Time Processing Module
######################

This module controls time-of-day on the
spacecraft, and acts as a software interface
to the RTC.

Requirements:
1 - The TPM shall always and only use UTC time.
2 - The TPM shall be the sole point of access to the RTC.
3 - The TPM shall be imported into applications when they require
time-of-day access.
4 - The TPM shall perform state correction based on GPS time whenever
the spacecraft gets a GPS fix.
5 - In the event of GPS failure, the TPM shall peform state corrections
through the command UPLINK_TIME_REFERENCE.
"""

import time

from core import logger
from hal.configuration import SATELLITE


class TIME_PROCESSOR:
    @classmethod
    def unix_time(self):
        if SATELLITE.RTC_AVAILABLE:
            return time.mktime(SATELLITE.RTC.datetime)
        else:
            logger.error("[TPM ERROR] RTC no longer active on SAT")
            return False
