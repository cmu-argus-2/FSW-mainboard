import time
from datetime import datetime, timedelta

from argusloop.magnetorquer import Magnetorquer
from argusloop.sensors import GPS, Gyroscope, Magnetometer, SunVector
from argusloop.spacecraft import Spacecraft


class Simulator:  # will be passed by reference to the emulated HAL
    def __init__(self):

        # self.read_configuration("nothing_for_now")

        config = {
            "mass": 1.5,
            "inertia": [10, 20, 10, 0.0, 0.0, 0.0],
            "epoch": datetime.now(),
            "dt": 0.01,
            "initial_attitude": [1.0, 0, 0, 0, 0.1, -0.2, 0.3],
            "initial_orbit_oe": [6.92e6, 0, 0, 0, 0, 0],
            "gravity_order": 10,
            "gravity_degree": 10,
            "drag": True,
            "third_body": True,
        }
        print(f"Here is the current satellite configuration:\n{config}")

        self.time = config["epoch"]
        self.base_dt = config["dt"]

        self.spacecraft = Spacecraft(config)
        self.last_ctrl = []

        # Need to init all simulated hardware

        self._magnetometer = Magnetometer(2.0)
        self._gyroscope = Gyroscope(0.01, 0.2, 0.5)
        self._sun_vec = SunVector(0.1, 0.0)
        self._gps = GPS(10, 0.1)
        self._torquer = Magnetorquer()

        print("Gyroscope: ", self._gyroscope.measure(self.spacecraft))
        print("Magnetometer: ", self._magnetometer.measure(self.spacecraft))
        print("Measured Lux: ", self._sun_vec.measure_lux(self.spacecraft))
        print("Measured Sun Vector: ", self._sun_vec.measure(self.spacecraft))
        print("GPS (ECEF): ", self._gps.measure(self.spacecraft))
        print("Dipole Moment (voltage): ", self._torquer.set_dipole_moment_voltage(4))
        print("Dipole Moment (current): ", self._torquer.set_dipole_moment_current(0.32))

    def gyro(self):
        self.advance_to_time()
        return self._gyroscope.measure(self.spacecraft)

    def mag(self):
        self.advance_to_time()
        return self._magnetometer.measure(self.spacecraft)

    def sun_vec(self):
        self.advance_to_time()
        return self._sun_vec.measure(self.spacecraft)

    def gps(self):
        self.advance_to_time()
        return self._gps.measure(self.spacecraft)

    def advance_to_time(self):
        time_diff = datetime.fromtimestamp(time.time()) - self.time
        # TODO Handle granularity
        iters = int(time_diff.total_seconds() / self.base_dt)
        # print(f"Advancing {iters} iterations")
        for _ in range(iters):
            self.spacecraft.advance([0.0, 0.0, 0.0])
        self.time += timedelta(seconds=(iters * self.base_dt))

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

    # sim.advance_to_time()
    print(sim.time)
