import builtins
import os


class SD:
    def __init__(self):
        try:
            os.mkdir("./sd")
        except Exception:
            pass
        self.open = builtins.open
        self.mkdir = os.mkdir

    def custom_open(self, filepath, string):
        if filepath[0] == "/":
            filepath = filepath[1:]
        return self.open(filepath, string)

    def custom_mkdir(self, filepath):
        if filepath[0] == "/":
            filepath = filepath[1:]
        self.mkdir(filepath)

    ######################## ERROR HANDLING ########################

    @property
    def device_errors(self):
        return []

    def deinit(self):
        return
