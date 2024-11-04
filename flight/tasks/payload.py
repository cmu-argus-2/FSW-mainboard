# Payload Control Task

from core import TemplateTask


class Task(TemplateTask):
    def __init__(self, id):
        super().__init__(id)
        self.name = "PAYLOAD"

    async def main_task(self):
        pass
