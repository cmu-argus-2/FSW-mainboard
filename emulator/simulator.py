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
import shutil
import time
from datetime import datetime

import numpy as np
from argusim.simulation_manager.sim import Simulator as cppSim

ARGUS_ROOT = os.getenv("ARGUS_ROOT", os.path.join(os.getcwd(), "../"))
RESULTS_ROOT_FOLDER = os.path.join(ARGUS_ROOT, "sil/results")
CONFIG_FILE = os.path.join(ARGUS_ROOT, "sil/configs/params.yaml")


class Simulator:  # will be passed by reference to the emulated HAL
    def __init__(self, trial=None, trial_date=None, sim_set_name="sil_set_1"):
        if trial is None:
            trial = random.randint(0, 100)
        if trial_date is None:
            trial_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        RESULTS_FOLDER = os.path.join(RESULTS_ROOT_FOLDER, trial_date, sim_set_name, "trials/trial" + str(trial))
        os.makedirs(RESULTS_FOLDER)
        shutil.copy(CONFIG_FILE, os.path.join(os.path.dirname(RESULTS_FOLDER), "../params.yaml"))
        self.cppsim = cppSim(trial, RESULTS_FOLDER, CONFIG_FILE, log=True)

        self.measurement = np.zeros((49,))
        self.starting_real_epoch = time.monotonic_ns() / 1.0e9
        self.latest_real_epoch = self.starting_real_epoch
        self.base_dt = self.cppsim.params.dt
        self.sim_time = 0

        # Measurement labels
        self.gps_idx = slice(0, 6)
        self.gyro_idx = slice(6, 9)
        self.mag_idx = slice(9, 12)
        self.lux_idx = slice(12, 21)
        self.mtb_idx = slice(21, 27)
        self.solar_idx = slice(27, 40)
        self.power_idx = slice(40, 48)
        self.jetson_idx = slice(48, 49)

    """
        SENSOR CALLBACKS
        Populate each sensor with the appropriate readings
        They also advance the c++ simulation before reading
    """

    def gyro(self):
        self.advance_to_time()
        return np.deg2rad(self.measurement[self.gyro_idx])  # IMU obtains gyro readins in deg/s

    def mag(self):
        self.advance_to_time()
        return self.measurement[self.mag_idx]  # IMU obtains magnetic field readings in uT

    def sun_lux(self, attr):
        self.advance_to_time()  # XP, XM, YP, YM, ZP1, ZP2, ZP3, ZP4, ZM

        attr2idx = {"XP": 0, "XM": 1, "YP": 2, "YM": 3, "ZP1": 4, "ZP2": 5, "ZP3": 6, "ZP4": 7, "ZM": 8}
        if attr not in attr2idx.keys():
            raise Exception(f"Invalid Sun Sensor dir {attr}")
        return self.measurement[self.lux_idx][attr2idx[attr]]

    def gps(self):
        self.advance_to_time()
        gps_state = np.array([self.get_sim_time()] + list(self.measurement[self.gps_idx] * 1e2))
        return gps_state  # GPS returns data in cm

    def coil_power(self, idx):
        self.advance_to_time()
        return self.measurement[self.mtb_idx][idx]

    def solar_power(self, attr):
        self.advance_to_time()
        power_idx_map = {
            "XP": [0, 5, 6],
            "XM": [1, 7, 8],
            "YP": [2, 9, 10],
            "YM": [3, 11, 12],
            "ZP": [4],
        }  # power monitors not on deployables
        if attr in power_idx_map.keys():
            voltage = self.measurement[self.power_idx][3]
            if voltage != 0:
                current = sum(self.measurement[self.solar_idx][power_idx_map[attr]]) / voltage
            else:
                current = 0
            return voltage, current
        else:
            raise Exception("Invalid Solar power monitor key")

    def jetson_power(self):
        self.advance_to_time()
        voltage = self.measurement[self.power_idx][3]
        if voltage != 0:
            current = self.measurement[self.jetson_idx] / voltage
        else:
            current = 0
        return (voltage, current)

    def battery_diagnostics(self, attr: str):
        self.advance_to_time()
        attr2idx = dict(
            zip(["soc", "capacity", "current", "voltage", "midvoltage", "tte", "ttf", "temperature"], [i for i in range(8)])
        )

        if self.measurement[self.power_idx][attr2idx["tte"]] > 1e7 or self.measurement[self.power_idx][attr2idx["tte"]] < 0:
            self.measurement[self.power_idx][attr2idx["tte"]] = 0
        if self.measurement[self.power_idx][attr2idx["ttf"]] > 1e7 or self.measurement[self.power_idx][attr2idx["ttf"]] < 0:
            self.measurement[self.power_idx][attr2idx["ttf"]] = 0

        if attr in attr2idx.keys():
            return self.measurement[self.power_idx][attr2idx[attr]]
        else:
            raise Exception("Invalid Battery diagnostic attribute")

    def set_control_input(self, dir, input):
        """
        Sets the control input to the simulation XP, XM, YP, YM, ZP, ZM
        """
        dir_2_idx_map = {"XP": 0, "XM": 1, "YP": 2, "YM": 3, "ZP": 4, "ZM": 5}
        self.cppsim.control_input[dir_2_idx_map[dir]] = input * 5

    def get_time_diff_since_last(self):
        """
        Time since last simulation advance
        """
        self.starting_real_epoch = time.monotonic_ns() / 1.0e9

        return self.starting_real_epoch - self.latest_real_epoch

    def advance_to_time(self):
        """
        Advance in steps of 'dt' to reach the current FSW time
        """
        time_diff = self.get_time_diff_since_last()
        iters = int(time_diff / self.base_dt)

        if iters > 20:
            iters = 20
            dt = iters * self.base_dt / 20
        else:
            dt = self.base_dt

        if iters != 0:
            self.latest_real_epoch += iters * dt

        for _ in range(iters):
            self.measurement = self.cppsim.step(self.sim_time, dt)
            self.sim_time += dt

    def get_sim_time(self):
        return 946728000 + self.cppsim.get_time()
