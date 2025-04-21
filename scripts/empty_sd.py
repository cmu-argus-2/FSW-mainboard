# Load the DH
from core import DataHandler as DH

# Boot Satellite
from hal.configuration import SATELLITE

SATELLITE.boot_sequence()

# Delete all files
DH.delete_all_files()
