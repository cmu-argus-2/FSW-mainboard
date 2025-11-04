import time

from hal.configuration import SATELLITE

print("Booting ARGUS...")
SATELLITE.boot_sequence()
print("ARGUS booted.")
print(f"Boot Errors: {SATELLITE.ERRORS}")

while True:
    time.sleep(1)
    for sensors in SATELLITE.DEPLOYMENT_SENSORS.keys():
        if SATELLITE.DEPLOYMENT_SENSOR_AVAILABLE(sensors):
            print(f"Deployment sensor {sensors}: {SATELLITE.DEPLOYMENT_SENSOR_DISTANCE(sensors)} cm")
