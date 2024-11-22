import os
import random
import time
from datetime import datetime, timedelta

import numpy as np
from argusim.simulation_manager.sim import Simulator as cppSim

RESULTS_ROOT_FOLDER = os.path.join(os.getenv("ARGUS_ROOT"), "results")
CONFIG_FILE = os.path.join(os.getenv("ARGUS_ROOT"), "params.yaml")


class Simulator:  # will be passed by reference to the emulated HAL
    def __init__(self):
        # Initialize the CPP sim
        trial = random.randint(0, 100)
        RESULTS_FOLDER = os.path.join(RESULTS_ROOT_FOLDER, datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        os.mkdir(RESULTS_FOLDER)
        self.cppsim = cppSim(trial, RESULTS_FOLDER, CONFIG_FILE)

        self.measurement = np.zeros((18,))
        self.starting_real_epoch = datetime.fromtimestamp(time.time())
        self.base_dt = self.cppsim.params.dt
        self.sim_time = 0

    """
        SENSOR CALLBACKS
        Populate each sensor with the appropriate readings
        They also advance the c++ simulation before reading
    """

    def gyro(self):
        self.advance_to_time()
        return self.measurement[6:9]

    def mag(self):
        self.advance_to_time()
        return self.measurement[9:12]

    def sun_lux(self):
        self.advance_to_time()
        return self.measurement[12:]

    def gps(self):
        self.advance_to_time()
        return self.measurement[0:6]

    def set_control_input(self, input):  # TODO : ADCS does not set a control input yet
        """
        Sets the control input to the simulation
        """
        self.cppsim.set_control_input(input)

    def get_time_diff_since_last(self):
        """
        Time since last simulation advance
        """
        self.latest_real_epoch = self.starting_real_epoch
        self.starting_real_epoch = datetime.fromtimestamp(time.time())
        return self.starting_real_epoch - self.latest_real_epoch

    def advance_to_time(self):
        """
        Advance in steps of 'dt' to rech the current FSW time
        """
        time_diff = self.get_time_diff_since_last()
        # TODO Handle granularity
        iters = int(time_diff.total_seconds() / self.base_dt)
        # print(f"Advancing {iters} iterations")
        for _ in range(iters):
            self.measurement = self.cppsim.step(self.sim_time, self.base_dt)
        self.sim_time += iters * self.base_dt


if __name__ == "__main__":

    sim = Simulator()

    tt = datetime.now()
    base_dt = 0.01

    print(tt)
    print(datetime.fromtimestamp(time.time()))

    for _ in range(1000):
        sim.set_control_input(np.random.random((7,)))
        sim.advance_to_time()
        time.sleep(0.08)

    # sim.advance_to_time()
    print(sim.sim_time)
