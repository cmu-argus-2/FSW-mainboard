import digitalio


class Watchdog:
    def __init__(self, enable_pin: object, interrupt: object):
        self.__enable = digitalio.DigitalInOut(enable_pin)
        self.__enable.direction = digitalio.Direction.OUTPUT
        self.__enable.value = False

        self.__interrupt = digitalio.DigitalInOut(interrupt)
        self.__interrupt.direction = digitalio.Direction.OUTPUT
        self.__interrupt.value = False

    def enable(self):
        self.__enable.value = True

    def disable(self):
        self.__enable.value = False

    def interrupt_high(self):
        self.__interrupt.value = True

    def interrupt_low(self):
        self.__interrupt.value = False
