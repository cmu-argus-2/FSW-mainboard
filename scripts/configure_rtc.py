import time

from hal.configuration import SATELLITE

# Time you want to set (NEEDS TO BE A UTC TIMESTAMP)
unix_timestamp = 1742166255

# Boot up SC
print("Booting ARGUS...")
SATELLITE.boot_sequence()
print("ARGUS booted.")
print(f"Boot Errors: {SATELLITE.ERRORS}")

# Set up RTC clock
SATELLITE.RTC.set_datetime(time.localtime(unix_timestamp))
