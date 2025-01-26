"""
Interface to connect the simulation backend of choice with the emulated hardware abstraction layer (HAL).

======================

This module provides the Simulator class passed to the emulated HAL to interact with the simulation backend.
The Simulator class initializes various simulated hardware components and provides methods to interact with them.
It automatically manages the simulation time and advances the simulation to the current real-world time.
Author(s): Ibrahima S. Sow

"""

import time
from datetime import datetime, timedelta

import numpy as np
from argusloop.magnetorquer import Magnetorquer
from argusloop.sensors import GPS, Gyroscope, Magnetometer, SunVector
from argusloop.spacecraft import Spacecraft


class Simulator:  # will be passed by reference to the emulated HAL
    """
    The Simulator class emulates the hardware abstraction layer (HAL) for a satellite simulation. It initializes
    various simulated hardware components and provides methods to interact with them.

    Attributes:
        starting_sim_epoch (datetime): The starting epoch of the simulation.
        starting_real_epoch (datetime): The real-world starting epoch of the simulation.
        latest_real_epoch (datetime): The latest real-world epoch recorded.
        sim_time (datetime): The current simulation time.
        base_dt (float): The base time step for the simulation.
        spacecraft (Spacecraft): The spacecraft being simulated.
        _last_sim_ctrl (numpy.ndarray): The last control input applied to the simulation.
        _magnetometer (Magnetometer): The simulated magnetometer.
        _gyroscope (Gyroscope): The simulated gyroscope.
        _sun_vec (SunVector): The simulated sun vector sensor.
        _gps (GPS): The simulated GPS sensor.
        _torquers (dict): A dictionary of simulated magnetorquers.

    Methods:
        gyro(): Measures the gyroscope data.
        mag(): Measures the magnetometer data.
        sun_vec(): Measures the sun vector data.
        sun_lux(): Measures the sun lux data.
        gps(): Measures the GPS data.
        set_coil_throttle(direction, throttle_volts): Sets the dipole moment voltage for a specified direction.
        set_torque_to_spacecraft(dipole_moment): Computes and applies torque to the spacecraft.
        _get_time_diff_since_last(): Calculates the time difference since the last recorded epoch.
        advance_to_time(): Advances the simulation to the current real-world time.
        read_configuration(config_file): Method for reading configuration from a file.
    """

    def __init__(self):
        # TODO self.read_configuration("nothing_for_now")

        config = {
            "mass": 1.5,
            "inertia": [10, 20, 10, 0.0, 0.0, 0.0],
            "epoch": datetime(2024, 6, 1, 12, 0, 0, 0),
            "dt": 0.01,
            "initial_attitude": [1.0, 0, 0, 0, 5.1, -9.2, 0.3],
            "initial_orbit_oe": [6.92e6, 0, 0, 0, 0, 0],
            "gravity_order": 5,
            "gravity_degree": 5,
            "drag": True,
            "third_body": True,
        }
        print(f"Here is the current satellite configuration:\n{config}")

        self.starting_sim_epoch = config["epoch"]
        self.starting_real_epoch = datetime.fromtimestamp(time.time())
        self.latest_real_epoch = self.starting_real_epoch
        self.sim_time = config["epoch"]
        self.base_dt = config["dt"]

        self.spacecraft = Spacecraft(config)
        self._last_sim_ctrl = np.zeros(3)

        # Initialize all simulated hardware from backend

        self._magnetometer = Magnetometer(2.0)
        self._gyroscope = Gyroscope(0.01, 0.2, 0.5)
        self._sun_vec = SunVector(0.1, 0.0)
        self._gps = GPS(10, 0.1)  # TODO rest of frame in argusloop
        self._torquers = {
            "XP": Magnetorquer(),
            "XM": Magnetorquer(),
            "YP": Magnetorquer(),
            "YM": Magnetorquer(),
            "ZM": Magnetorquer(),
            "ZP": Magnetorquer(),
        }

    def gyro(self) -> np.ndarray:
        """
        Measures the gyroscope data.

        Returns:
            np.ndarray: The measured gyroscope data.
        """
        self.advance_to_time()
        return self._gyroscope.measure(self.spacecraft)

    def mag(self) -> np.ndarray:
        """
        Measures the magnetometer data.

        Returns:
            np.ndarray: The measured magnetometer data.
        """
        self.advance_to_time()
        return self._magnetometer.measure(self.spacecraft)

    def sun_vec(self) -> np.ndarray:
        """
        Measures the sun vector data.

        Returns:
            np.ndarray: The measured sun vector data.
        """
        self.advance_to_time()
        return self._sun_vec.measure(self.spacecraft)

    def sun_lux(self) -> float:
        """
        Measures the sun lux data.

        Returns:
            float: The measured sun lux data.
        """
        self.advance_to_time()
        return self._sun_vec.measure_lux(self.spacecraft)

    def gps(self) -> dict:
        """
        Measures the GPS data.

        Returns:
            dict: The measured GPS data.
        """
        self.advance_to_time()
        return self._gps.measure(self.spacecraft)

    def set_coil_throttle(self, direction: str, throttle_volts: float) -> None:
        """
        Sets the dipole moment voltage for a specified direction.

        Args:
            direction (str): The direction of the magnetorquer.
            throttle_volts (float): The voltage to set for the dipole moment.
        """
        return self._torquers[direction].set_dipole_moment_voltage(throttle_volts)

    def set_torque_to_spacecraft(self, dipole_moment: np.ndarray) -> None:
        """
        Computes and applies torque to the spacecraft.

        Args:
            dipole_moment (np.ndarray): The dipole moment to apply.
        """
        self.advance_to_time()
        self._last_sim_ctrl = self.spacecraft.compute_torque(dipole_moment)

    def _get_time_diff_since_last(self) -> timedelta:
        """
        Calculates the time difference since the last recorded epoch.

        Returns:
            timedelta: The time difference since the last recorded epoch.
        """
        self.latest_real_epoch = self.starting_real_epoch
        self.starting_real_epoch = datetime.fromtimestamp(time.time())
        return self.starting_real_epoch - self.latest_real_epoch

    def advance_to_time(self) -> None:
        """
        Advances the simulation to the current real-world time.
        """
        time_diff = self._get_time_diff_since_last()
        iters = int(time_diff.total_seconds() / self.base_dt)
        for _ in range(iters):
            self.spacecraft.advance(self._last_sim_ctrl)
        self.sim_time += timedelta(seconds=(iters * self.base_dt))

    def read_configuration(self, config_file: str) -> None:
        """
        Reads configuration from a file.

        Args:
            config_file (str): The path to the configuration file.
        """
        pass


if __name__ == "__main__":
    sim = Simulator()

    tt = datetime.now()
    base_dt = 0.01

    print(tt)
    print(datetime.fromtimestamp(time.time()))

    for _ in range(1000):
        sim.advance_to_time()
        time.sleep(0.08)
        print(sim.sun_lux())
        print(sim.sim_time)

    # sim.advance_to_time()
    print(sim.sim_time)
