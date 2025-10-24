import digitalio
import hal.drivers.errors as Errors


class Watchdog:
    def __init__(self, enable_pin: object, input: object):
        self.__enable = digitalio.DigitalInOut(enable_pin)
        self.__enable.direction = digitalio.Direction.OUTPUT
        self.__enable.value = False
        self.__en_val = False  # Error handling

        self.__input = digitalio.DigitalInOut(input)
        self.__input.direction = digitalio.Direction.OUTPUT
        self.__input.value = True
        self.__input_val = True  # Error handling

    def enable(self):
        self.__enable.value = True
        self.__en_val = True

    @property
    def enabled(self):
        return self.__enable.value

    def disable(self):
        self.__enable.value = False
        self.__en_val = False

    def input_high(self):
        self.__input.value = True
        self.__input_val = True

    def input_low(self):
        self.__input.value = False
        self.__input_val = False

    @property
    def input(self):
        return self.__input.value

    ######################## ERROR HANDLING ########################

    @property
    def device_errors(self):
        results = []
        if self.__en_val != self.__enable.value:
            results.append(Errors.WATCHDOG_EN_GPIO_ERROR)
        if self.__input_val != self.__input.value:
            results.append(Errors.WATCHDOG_INPUT_GPIO_ERROR)
        return results

    def deinit(self):
        self.__enable.deinit()
        self.__enable = None
        self.__input.deinit()
        self.__input = None
        return
