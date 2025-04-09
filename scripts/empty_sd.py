import os

# Boot Satellite
from hal.configuration import SATELLITE
SATELLITE.boot_sequence()

# Load the DH
from core import DataHandler as DH

# Delete all files
DH.delete_all_files()

