class FuelGauge:
    def __init__(self):
        self.voltage = 7800.0
        self.current = 10.0
        self.midvoltage = 0.0

        self.soc = 90
        self.capacity = 0
        self.cycles = 0
        self.tte = 10000
        self.ttf = 2500
        self.time_pwrup = 0
        self.temperature = 35.0

    def read_soc(self):
        """
        Reads SoC from the battery pack.

        :return: SoC as a percentage.
        """
        return self.soc

    def read_capacity(self):
        """
        Reads capacity from the battery pack.

        :return: Capacity in mAh.
        """
        return self.capacity

    def read_current(self):
        """
        Reads the current from the battery pack.

        :return: Current in mA as a float.
        """
        return self.current

    def read_voltage(self):
        """
        Reads the voltage for the battery pack.

        :return: Voltage in mV as a float.
        """
        return self.voltage

    def read_midvoltage(self):
        """
        Reads the midpoint voltage for the battery pack.

        :return: Voltage in mV as a float.
        """
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
        return self.tte

    def read_ttf(self):
        """
        Reads the time-to-full for the battery pack.

        :return: Time-to-full in seconds
        """
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
        return self.temperature

    def reset(self):
        pass
