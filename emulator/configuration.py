import os

from core import DataHandler as DH
from hal.cubesat import CubeSat
from hal.emulator import EmulatedSatellite

DH.sd_path = "sd"

# Enable for Middleware
DEBUG_MODE = True
EN_MIDDLEWARE = True
SIMULATION = bool(int(os.getenv("ARGUS_SIMULATION_FLAG", 0)))
SOCKET_RADIO = False

SimulatedSpacecraft = None
if SIMULATION:
    from hal.simulator import Simulator

    SimulatedSpacecraft = Simulator()

SATELLITE: CubeSat = EmulatedSatellite(
    enable_middleware=EN_MIDDLEWARE, debug=DEBUG_MODE, simulator=SimulatedSpacecraft, use_socket=SOCKET_RADIO
)
