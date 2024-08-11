# TODO Logging


class TemplateTask:
    """
    A Task Object.

    Attributes:
        ID:          Unique identifier for the task.
        name:        Name of the task object.
    """

    ID = 0xFF
    name = "TEMPLATE TASK"

    def __init__(self, id):
        self.ID = id

    def debug(self, msg):
        """
        Print a debug message formatted with the task name

        :param msg: Debug message to print
        :param level: > 1 will print as a sub-level
        """
        print(f"[{self.ID}][{self.name}] Error: {msg}")

    async def main_task(self, *args, **kwargs):
        """
        Contains the code for the user defined task.

        :param `*args`: Variable number of arguments used for task execution.
        :param `**kwargs`: Variable number of keyword arguments used for task execution.
        """
        pass

    async def _run(self):
        """
        Try to run the main task, then call handle_error if an error is raised.
        """
        try:
            await self.main_task()
        except Exception as e:
            # TODO change this to comply with the logging system of the framework
            self.debug(f"{e}")
