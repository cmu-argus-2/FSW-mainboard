import time

from hal.configuration import SATELLITE

print("Booting ARGUS...")
SATELLITE.boot_sequence()
print("ARGUS booted.")
print(f"Boot Errors: {SATELLITE.ERRORS}")

# Turning on
# print("Turning on the Jetson...")
# SATELLITE.JETSON_ENABLE.value = True
# time.sleep(0.1)  # TODO: probably do not need this delay
# SATELLITE.JETSON_SD_REQ.value = True  # turn of 5v dcdc to save more power
# print("Jetson should be on now.")

# Turning off
print("Turning off the Jetson...")
SATELLITE.JETSON_ENABLE.value = False
time.sleep(0.1)  # TODO: probably do not need this delay
SATELLITE.JETSON_SD_REQ.value = False  # turn off the 5v regulator to save power
print("Jetson should be off now.")

while True:
    time.sleep(1)