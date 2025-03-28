"""
Interface to connect the simulation backend of choice with the emulated hardware abstraction layer (HAL).

======================

This module provides the Simulator class passed to the emulated HAL to interact with the simulation backend.
The Simulator class initializes various simulated hardware components and provides methods to interact with them.
It automatically manages the simulation time and advances the simulation to the current real-world time.
Author(s): Karthik Karumanchi, Ibrahima S. Sow

"""

import os
import random
import time
from datetime import datetime

import numpy as np
from argusim.simulation_manager.sim import Simulator as cppSim

ARGUS_ROOT = os.getenv("ARGUS_ROOT", os.path.join(os.getcwd(), "../"))
RESULTS_ROOT_FOLDER = os.path.join(ARGUS_ROOT, "results")
CONFIG_FILE = os.path.join(ARGUS_ROOT, "params.yaml")


class Simulator:  # will be passed by reference to the emulated HAL
    def __init__(self):
        # Initialize the CPP sim
        trial = random.randint(0, 100)
        RESULTS_FOLDER = os.path.join(RESULTS_ROOT_FOLDER, datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        os.mkdir(RESULTS_FOLDER)
        self.cppsim = cppSim(trial, RESULTS_FOLDER, CONFIG_FILE)

        self.measurement = np.zeros((18,))
        self.starting_real_epoch = time.time_ns() / 1.0e9
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
        return self.measurement[9:12] * 1e6  # IMU obtains magnetic field readings in uT

    def sun_lux(self):
        self.advance_to_time()
        return self.measurement[12:]

    def gps(self):
        self.advance_to_time()
        gps_state = np.array([time.time()] + list(self.measurement[0:6] * 1e2))
        return gps_state  # GPS returns data in cm

    def set_control_input(self, dir, input):
        """
        Sets the control input to the simulation
        """
        dir_2_idx_map = {"XM": 0, "YM": 1, "ZM": 2, "XP": 3, "YP": 4, "ZP": 5}
        self.cppsim.control_input[dir_2_idx_map[dir]] = input * 5

    def get_time_diff_since_last(self):
        """
        Time since last simulation advance
        """
        self.latest_real_epoch = self.starting_real_epoch
        self.starting_real_epoch = self.base_dt * ((time.time_ns() / 1.0e9) // self.base_dt)
        return self.starting_real_epoch - self.latest_real_epoch

    def advance_to_time(self):
        """
        Advance in steps of 'dt' to rech the current FSW time
        """
        time_diff = self.get_time_diff_since_last()
        # TODO Handle granularity
        iters = int(time_diff / self.base_dt)
        # print(f"Advancing {iters} iterations")
        for _ in range(iters):
            self.measurement = self.cppsim.step(self.sim_time, self.base_dt)
        self.sim_time += iters * self.base_dt
