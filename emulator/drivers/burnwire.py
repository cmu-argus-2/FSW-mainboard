class BurnWires:
    def __init__(self) -> None:
        return

    def duty_cycle(self, duty_cycle):
        assert 0 <= duty_cycle <= 0xFFFF

    def set_pwm(self, x, y):
        return

    def enable_driver(self):
        return

    def disable_driver(self):
        return

    ######################## ERROR HANDLING ########################

    @property
    def device_errors(self):
        return []

    def deinit(self):
        return
