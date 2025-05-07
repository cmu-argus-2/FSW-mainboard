# Hardware watchdog task
# This task is responsible for toggling the hardware watchdog pin to prevent
# the system from resetting unexpectedly and to ensure that the system is
# functioning correctly.

from core import TemplateTask
from hal.configuration import SATELLITE

_WAIT_CYCLE = 1  # wait cycles so the pin is toggled before the enable pin


class Task(TemplateTask):
    def __init__(self, id):
        super().__init__(id)
        self.name = "WATCHDOG"
        self.counter = 0

    async def main_task(self):
        if SATELLITE.WATCHDOG_AVAILABLE:

            """
            The enable pin is used for a MOSFET to control the signal to the
            MCU, the watchdog is powered regardless of the enable pin.
            The input pin will therefore need to be toggled before the enable pin
            is toggled to ensure that the watchdog is not triggered during the
            transition.
            """

            if SATELLITE.WATCHDOG.input:
                SATELLITE.WATCHDOG.input_low()
            else:
                SATELLITE.WATCHDOG.input_high()

            if not SATELLITE.WATCHDOG.enabled and self.counter > _WAIT_CYCLE:
                self.log_info("Watchdog enabled.")
                SATELLITE.WATCHDOG.enable()

            self.counter += 1
