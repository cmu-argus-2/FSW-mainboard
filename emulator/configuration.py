import os

from hal.cubesat import CubeSat
from hal.emulator import EmulatedSatellite

# from core import DataHandler as DH


# DH.sd_path = "sd"

DEBUG_MODE = True
SIMULATION = bool(int(os.getenv("ARGUS_SIMULATION_FLAG", 0)))
SOCKET_RADIO = False

SimulatedSpacecraft = None
if SIMULATION:
    # if there is a trial flag, use it to create the simulator
    import random
    from datetime import datetime

    from hal.simulator import Simulator

    trial = int(os.getenv("ARGUS_SIMULATION_TRIAL", random.randint(0, 100)))
    trial_date = os.getenv("ARGUS_SIMULATION_DATE", datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    sim_set_name = os.getenv("ARGUS_SIMULATION_SET_NAME", "sil_set_1")
    SimulatedSpacecraft = Simulator(trial=trial, trial_date=trial_date, sim_set_name=sim_set_name)

SATELLITE: CubeSat = EmulatedSatellite(debug=DEBUG_MODE, simulator=SimulatedSpacecraft, use_socket=SOCKET_RADIO)
