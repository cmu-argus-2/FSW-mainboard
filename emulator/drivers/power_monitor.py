class PowerMonitor:
    def __init__(self, device_name: str, voltage: float = 0, current: float = 0, simulator=None) -> None:
        self.__device_name = device_name
        self.__voltage = voltage
        self.__current = current
        self.__simulator = simulator

    def read_voltage_current(self):
        if self.__simulator is not None:
            if self.__device_name in ["XP", "XM", "YP", "YM", "ZP"]:
                self.__voltage, self.__current = self.__simulator.solar_power(self.__device_name)
            elif self.__device_name == "JETSON":
                self.__voltage, self.__current = self.__simulator.jetson_power()
        return (self.__voltage, self.__current)

    ######################## ERROR HANDLING ########################

    @property
    def device_errors(self):
        return []

    def deinit(self):
        return
