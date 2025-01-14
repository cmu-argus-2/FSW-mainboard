# Hardware watchdog and HAL monitor task
# This task is responsible for monitoring the health of the hardware abstraction layer (HAL),
# performing diagnostics in case of failure, and reporting/logging HAL status.

from core import TemplateTask


class Task(TemplateTask):
    def __init__(self, id):
        super().__init__(id)
        self.name = "WATCHDOG"

    async def main_task(self):
        pass
