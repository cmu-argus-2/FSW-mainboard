import os

from hal.cubesat import CubeSat
from hal.emulator import EmulatedSatellite
from hal.simulator import Simulator

# from core import DataHandler as DH


# DH.sd_path = "sd"

# Enable for Middleware
DEBUG_MODE = True
EN_MIDDLEWARE = True
SIMULATION = bool(int(os.getenv("ARGUS_SIMULATION_FLAG", 0)))
SOCKET_RADIO = False

SimulatedSpacecraft: Simulator = None
if SIMULATION:
    SimulatedSpacecraft = Simulator()

SATELLITE: CubeSat = EmulatedSatellite(debug=DEBUG_MODE, simulator=SimulatedSpacecraft, use_socket=SOCKET_RADIO)
