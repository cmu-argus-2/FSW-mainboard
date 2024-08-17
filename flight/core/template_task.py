from core import logger


class TemplateTask:
    """
    A Task Object.

    Attributes:
        ID:          Unique identifier for the task.
        name:        Name of the task object.
    """

    def __init__(self, id, name="TASK"):
        self.ID = id
        self.name = name

    def debug(self, msg):
        """
        Print a debug message formatted with the task name, filename, and line number

        :param msg: Debug message to print
        :param level: > 1 will print as a sub-level
        """
        logger.info(f"[{self.ID}][{self.name}] {msg}")

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
            self.debug(f"{e}")

    def log_debug(self, msg):
        """
        Log a debug message with the task name

        :param msg: Message to log
        """
        logger.debug(f"[{self.ID}][{self.name}] {msg}")

    def log_info(self, msg):
        """
        Log a message with the task name

        :param msg: Message to log
        """
        logger.info(f"[{self.ID}][{self.name}] {msg}")

    def log_warning(self, msg):
        """
        Log a warning message with the task name

        :param msg: Message to log
        """
        logger.warning(f"[{self.ID}][{self.name}] {msg}")

    def log_error(self, msg):
        """
        Log an error message with the task name

        :param msg: Message to log
        """
        logger.error(f"[{self.ID}][{self.name}] {msg}")

    def log_critical(self, msg):
        """
        Log a critical message with the task name

        :param msg: Message to log
        """
        logger.critical(f"[{self.ID}][{self.name}] {msg}")
