import digitalio
import hal.drivers.errors as Errors


class Watchdog:
    def __init__(self, enable_pin: object, input: object):
        self.__enable_pin = enable_pin

        self.__enable = digitalio.DigitalInOut(enable_pin)
        self.__enable.switch_to_output(True, digitalio.DriveMode.PUSH_PULL)
        self.__en_val = True  # Error handling

        self.__input = digitalio.DigitalInOut(input)
        self.__input.direction = digitalio.Direction.OUTPUT
        self.__input.value = False
        self.__input_val = False  # Error handling

    def enable(self):
        if not self.__en_val:
            self.__enable = digitalio.DigitalInOut(self.__enable_pin)
            self.__enable.switch_to_output(True, digitalio.DriveMode.PUSH_PULL)
            self.__en_val = True

    def disable(self):
        if self.__en_val:
            self.__enable.deinit()
            self.__en_val = False

    @property
    def enabled(self):
        return self.__en_val

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
        if self.__en_val:
            self.__enable.deinit()
            self.__enable = None
            self.__en_val = False
        self.__input.deinit()
        self.__input = None
        self.__input_val = False
        return
