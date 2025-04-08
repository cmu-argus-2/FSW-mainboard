import digitalio


class BatteryHeaters:
    def __init__(self, enable_pin: object, HEAT0_EN: object, HEAT1_EN: object = None):
        self.__enable = digitalio.DigitalInOut(enable_pin)
        self.__enable.direction = digitalio.Direction.OUTPUT
        self.__enable.value = False

        self.__heater0_en = digitalio.DigitalInOut(HEAT0_EN)
        self.__heater0_en.direction = digitalio.Direction.OUTPUT
        self.__heater0_en.value = False

        if HEAT1_EN is not None:
            self.__heater1_en = digitalio.DigitalInOut(HEAT1_EN)
            self.__heater1_en.direction = digitalio.Direction.OUTPUT
            self.__heater1_en.value = False
        else:
            self.__heater1_en = None

    def enable_heater0(self):
        if not self.__enable.value:
            self.__enable.value = True
        self.__heater0_en.value = True

    def enable_heater1(self):
        if not self.__enable.value:
            self.__enable.value = True
        if self.__heater1_en is not None:
            self.__heater1_en.value = True

    def disable_heater0(self):
        self.__heater0_en.value = False
        if not self.__heater1_en.value:
            self.__enable.value = False

    def disable_heater1(self):
        self.__heater1_en.value = False
        if not self.__heater0_en.value:
            self.__enable.value = False

    def heater0_enabled(self):
        return self.__heater0_en.value and self.__enable.value

    def heater1_enabled(self):
        return self.__heater1_en.value and self.__enable.value if self.__heater1_en is not None else False
