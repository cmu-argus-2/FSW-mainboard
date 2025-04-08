import digitalio


class Watchdog:
    def __init__(self, enable_pin: object, input: object):
        self.__enable = digitalio.DigitalInOut(enable_pin)
        self.__enable.direction = digitalio.Direction.OUTPUT
        self.__enable.value = False

        self.__input = digitalio.DigitalInOut(input)
        self.__input.direction = digitalio.Direction.OUTPUT
        self.__input.value = False

    def enable(self):
        self.__enable.value = True

    def disable(self):
        self.__enable.value = False

    def input_high(self):
        self.__input.value = True

    def input_low(self):
        self.__input.value = False
