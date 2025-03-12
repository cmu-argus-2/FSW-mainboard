from time import struct_time


class RTC:
    def __init__(self, date_input: struct_time) -> None:
        self.datetime = date_input

    def datetime(self):
        return self.datetime

    def set_datetime(self, date_input: struct_time):
        self.datetime = date_input
