"""
Time Processing Module (TPM)
############################

This module controls acts as a software interface to the RTC and
an alternate source for time-of-day in case of RTC failures.

Requirements:
1 - The TPM shall always and only use UTC time.

2 - The TPM shall be the sole point of access to the RTC.

3 - The TPM shall be imported into applications when they require
time-of-day access.

4 - The TPM shall perform state correction using GPS time if the
spacecraft gets a fix and the difference between RTC and GPS time is
significant (> 10s), in an effort to conserve write cycles to the RTC.

5 - In the event of GPS failure, the TPM shall peform state corrections
through the command UPLINK_TIME_REFERENCE.

6 - In the event of RTC failure, the TPM shall perform best-effort
time-keeping using the last known TPM time reference as an offset for
time.time(), although this would be a last resort.

7 - The TPM offset shall also be updated for state correction using
GPS time or an uplinked time reference.
"""

import time

from hal.configuration import SATELLITE


class TimeProcessor:
    """
    time_reference: Last known TPM time, either from
    the last RTC reading or from the commanding task
    (on boot) if the RTC has failed.
    """

    # Initialize time_reference to 0
    time_reference = 0

    """
    time_offset: Offset between time.time() and
    time_reference, calculated whenever the RTC is
    available or state correction occurs.
    """

    # Initialize time_offset to 0
    time_offset = 0

    """
    Name: set_time
    Description: Set RTC time
    """

    @classmethod
    def set_time(self, unix_timestamp):
        if SATELLITE.RTC_AVAILABLE:
            # RTC exists, set RTC time
            SATELLITE.RTC.set_datetime(time.localtime(unix_timestamp))
        else:
            # RTC does not exist, update TPM time reference
            pass

    """
        Name: time
        Description: Return RTC time
    """

    @classmethod
    def time(self):
        if SATELLITE.RTC_AVAILABLE:
            # RTC exists, return RTC time
            return time.mktime(SATELLITE.RTC.datetime)
        else:
            # TODO: TPM time offset
            return time.time()
