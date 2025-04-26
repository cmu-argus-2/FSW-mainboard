from numpy import array


class IMU:
    def __init__(self, simulator=None) -> None:
        self.__simulator = simulator

        self.__mag = array([4.0, 3.0, 1.0])
        self.__gyro = array([0.0, 0.0, 0.0])
        self.__temp = 20
        self.__enable = False

        self.__accel = array([0.0, 0.0, 0.0])

    def accel(self):
        return self.__accel if self.__enable else None

    def mag(self):
        if self.__simulator:
            return self.__simulator.mag()
        return self.__mag if self.__enable else None

    def gyro(self):
        if self.__simulator:
            return self.__simulator.gyro()
        return self.__gyro if self.__enable else None

    def temperature(self):
        return self.__temp if self.__enable else None

    def enable(self):
        self.__enable = True

    def disable(self):
        self.__enable = False

    ######################## ERROR HANDLING ########################

    @property
    def device_errors(self):
        return []

    def deinit(self):
        return
