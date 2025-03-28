from time import gmtime, struct_time


class RTC:
    def __init__(self, date_input: struct_time) -> None:
        self.current_datetime = date_input

    @property
    def datetime(self):
        self.current_datetime = gmtime()
        return self.current_datetime

    def set_datetime(self, date_input: struct_time):
        self.datetime = date_input
