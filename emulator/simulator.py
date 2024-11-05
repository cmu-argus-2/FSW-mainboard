import time
from datetime import datetime, timedelta

import numpy as np
from argusloop.magnetorquer import Magnetorquer
from argusloop.sensors import GPS, Gyroscope, Magnetometer, SunVector
from argusloop.spacecraft import Spacecraft


class Simulator:  # will be passed by reference to the emulated HAL
    def __init__(self):

        # TODO self.read_configuration("nothing_for_now")

        config = {
            "mass": 1.5,
            "inertia": [10, 20, 10, 0.0, 0.0, 0.0],
            "epoch": datetime(2024, 6, 1, 12, 0, 0, 0),
            "dt": 0.01,
            "initial_attitude": [1.0, 0, 0, 0, 0.1, -0.2, 0.3],
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

        # Need to init all simulated hardware

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

    def gyro(self):
        self.advance_to_time()
        return self._gyroscope.measure(self.spacecraft)

    def mag(self):
        self.advance_to_time()
        return self._magnetometer.measure(self.spacecraft)

    def sun_vec(self):
        self.advance_to_time()
        return self._sun_vec.measure(self.spacecraft)

    def sun_lux(self):
        self.advance_to_time()
        return self._sun_vec.measure_lux(self.spacecraft)

    def gps(self):
        self.advance_to_time()
        return self._gps.measure(self.spacecraft)

    def set_coil_throttle(self, direction, throttle_volts):
        return self._torquers[direction].set_dipole_moment_voltage(throttle_volts)

    def set_torque_to_spacecraft(self, dipole_moment):
        self.advance_to_time()
        self._last_sim_ctrl = self.spacecraft.compute_torque(dipole_moment)

    def get_time_diff_since_last(self):
        self.latest_real_epoch = self.starting_real_epoch
        self.starting_real_epoch = datetime.fromtimestamp(time.time())
        return self.starting_real_epoch - self.latest_real_epoch

    def advance_to_time(self):
        time_diff = self.get_time_diff_since_last()
        # TODO Handle granularity
        iters = int(time_diff.total_seconds() / self.base_dt)
        # print(f"Advancing {iters} iterations")
        for _ in range(iters):
            self.spacecraft.advance(self._last_sim_ctrl)
        self.sim_time += timedelta(seconds=(iters * self.base_dt))

    def checkout_ctrl(self):
        pass

    def advance(self, ctrl):
        # Need to gather all magnetorquers here if different from 0
        # apply the control to the spacecraft
        # advance the sim
        pass

    def read_configuration(self, config_file):
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
