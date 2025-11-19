"""

Argus Battery Heaters Wrapper Driver

* Author(s): Perrin Tong

"""

import digitalio
from hal.drivers.errors import Errors


class BatteryHeaters:
    def __init__(self, enable_pin: object, HEAT0_EN: object, HEAT1_EN: object = None):
        self.__enable = digitalio.DigitalInOut(enable_pin)
        self.__enable.direction = digitalio.Direction.OUTPUT
        self.__enable.value = False
        self.__en_val = False  # Error handling

        self.__heater0_en = digitalio.DigitalInOut(HEAT0_EN)
        self.__heater0_en.direction = digitalio.Direction.OUTPUT
        self.__heater0_en.value = False
        self.__heater0_en_val = False  # Error handling

        # Heater 1 is optional, this driver supports single or dual heater configurations
        if HEAT1_EN is not None:
            self.__heater1_en = digitalio.DigitalInOut(HEAT1_EN)
            self.__heater1_en.direction = digitalio.Direction.OUTPUT
            self.__heater1_en.value = False
            self.__heater1_en_val = False  # Error handling
        else:
            self.__heater1_en = None

    def enable_heater0(self):
        if not self.__enable.value:
            self.__enable.value = True
            self.__en_val = True
        self.__heater0_en.value = True
        self.__heater0_en_val = True

    def enable_heater1(self):
        if self.__heater1_en is not None:
            if not self.__enable.value:
                self.__enable.value = True
                self.__en_val = True
            self.__heater1_en.value = True
            self.__heater1_en_val = True

    def disable_heater0(self):
        self.__heater0_en.value = False
        self.__heater0_en_val = False
        if not self.__heater1_en.value:
            self.__enable.value = False
            self.__en_val = False

    def disable_heater1(self):
        if self.__heater1_en is not None:
            self.__heater1_en.value = False
            self.__heater1_en_val = False
            if not self.__heater0_en.value:
                self.__enable.value = False
                self.__en_val = False

    def heater0_enabled(self):
        return self.__heater0_en.value and self.__enable.value

    def heater1_enabled(self):
        return self.__heater1_en.value and self.__enable.value if self.__heater1_en is not None else False

    ######################## ERROR HANDLING ########################

    @property
    def device_errors(self):
        results = []
        if self.__enable.value != self.__en_val:
            results.append(Errors.BATT_HEATER_EN_GPIO_ERROR)
        if self.__heater0_en.value != self.__heater0_en_val:
            results.append(Errors.BATT_HEATER_HEAT0_GPIO_ERROR)
        if self.__heater1_en is not None and self.__heater1_en.value != self.__heater1_en_val:
            results.append(Errors.BATT_HEATER_HEAT1_GPIO_ERROR)
        return results

    def deinit(self):
        self.__enable.deinit()
        self.__enable = None
        self.__heater0_en.deinit()
        self.__heater0_en = None
        if self.__heater1_en is not None:
            self.__heater1_en.deinit()
            self.__heater1_en = None
        return
