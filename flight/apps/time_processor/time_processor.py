"""
Time Processing Module
######################

This module controls time-of-day on the
spacecraft, and acts as a software interface
to the RTC.

Requirements:
1 - The time module shall be the sole point of access to the RTC.
2 - The time module shall be imported into applications when they require
time-of-day access.
3 - The time module shall perform state correction based on GPS time whenever
the spacecraft gets a GPS fix.
4 - In the event of GPS failure, the time module shall peform state corrections
through the command UPLINK_TIME_REFERENCE.
"""
