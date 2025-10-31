class LightSensor:
    def __init__(self, id, simulator=None) -> None:
        self.__simulator = simulator
        self.__lux = 0
        self.__id = id

    def lux(self):
        if self.__simulator is not None:
            return self.__simulator.sun_lux(self.__id)
        return self.__lux
