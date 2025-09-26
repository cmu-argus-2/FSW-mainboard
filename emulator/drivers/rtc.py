from time import gmtime, struct_time


class RTC:
    def __init__(self, date_input: struct_time, simulator=None) -> None:
        self.current_datetime = date_input
        self.__simulator = simulator

    @property
    def datetime(self):
        if self.__simulator is not None:
            unix_time = self.__simulator.get_sim_time()
            self.current_datetime = gmtime(unix_time)
        else:
            self.current_datetime = gmtime()
        return self.current_datetime

    def set_datetime(self, date_input: struct_time):
        self.datetime = date_input
