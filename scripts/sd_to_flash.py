import os
import time

import storage
from core import DataHandler as DH
from hal.configuration import SATELLITE

print("Booting ARGUS...")
SATELLITE.boot_sequence()
print("ARGUS booted.")
print(f"Boot Errors: {SATELLITE.ERRORS}")

while True:
    try:
        SATELLITE.NEOPIXEL.fill([255, 0, 0])
        storage.remount("/", True, True)  # Flash mode
        SATELLITE.NEOPIXEL.fill([0, 0, 255])
        DH.move_all_files_to_flash()
        print("Copy complete.")
        SATELLITE.NEOPIXEL.fill([0, 255, 0])
        break
    except Exception as e:
        print(f"Error: {e}")
        print("Retrying in 5 seconds...")
        time.sleep(5)
