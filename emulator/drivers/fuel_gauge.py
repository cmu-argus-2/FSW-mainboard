class FuelGauge:
    def __init__(self, simulator=None):
        self.voltage = 7800.0
        self.current = 10.0
        self.midvoltage = 0.0

        self.soc = 70
        self.capacity = 0
        self.cycles = 0
        self.tte = 10000
        self.ttf = 2500
        self.time_pwrup = 0
        self.temperature = 35.0

        self.simulator = simulator

    def read_soc(self):
        """
        Reads SoC from the battery pack.

        :return: SoC as a percentage.
        """
        if self.simulator is not None:
            self.soc = self.simulator.battery_diagnostics("soc")
        return self.soc

    def read_capacity(self):
        """
        Reads capacity from the battery pack.

        :return: Capacity in mAh.
        """
        if self.simulator is not None:
            voltage = self.simulator.battery_diagnostics("voltage")
            if voltage != 0:

                self.capacity = self.simulator.battery_diagnostics("capacity") / (
                   voltage * 3.6
                )  # in mAh
            else:
                self.capacity = 0
        return self.capacity

    def read_current(self):
        """
        Reads the current from the battery pack.

        :return: Current in mA as a float.
        """
        if self.simulator is not None:
            self.current = self.simulator.battery_diagnostics("current") * 1000  # in mA
        return self.current

    def read_voltage(self):
        """
        Reads the voltage for the battery pack.

        :return: Voltage in mV as a float.
        """
        if self.simulator is not None:
            self.voltage = self.simulator.battery_diagnostics("voltage") * 1000  # in mV
        return self.voltage

    def read_midvoltage(self):
        """
        Reads the midpoint voltage for the battery pack.

        :return: Voltage in mV as a float.
        """
        if self.simulator is not None:
            self.midvoltage = self.simulator.battery_diagnostics("midvoltage") * 1000  # in mV
        return self.midvoltage

    def read_cycles(self):
        """
        Reads the battery cycles for the battery pack.

        :return: Number of cycles.
        """
        return self.cycles

    def read_tte(self):
        """
        Reads the time-to-empty for the battery pack.

        :return: Time-to-empty in seconds
        """
        if self.simulator is not None:
            self.tte = self.simulator.battery_diagnostics("tte")
        return self.tte

    def read_ttf(self):
        """
        Reads the time-to-full for the battery pack.

        :return: Time-to-full in seconds
        """
        if self.simulator is not None:
            self.ttf = self.simulator.battery_diagnostics("ttf")
        return self.ttf

    def read_time_pwrup(self):
        """
        Reads the time since power up for the battery pack.

        :return: Time since power up in seconds
        """
        return self.time_pwrup

    def read_temperature(self):
        """
        Reads the temperature of the battery pack.

        :return: Temperature of the battery pack in Celsius
        """
        if self.simulator is not None:
            self.temperature = 100 * (self.simulator.battery_diagnostics("temperature") - 273.16)  # in cC
        return self.temperature

    def reset(self):
        pass
