class DeploymentSensor:
    def __init__(self, id, simulator=None) -> None:
        self.__simulator = simulator
        self.__distance = 0
        self.__id = id

    def distance(self):
        if self.__simulator is not None:
            return self.__simulator.deployment_sensor(self.__id)
        return self.__distance / 10
