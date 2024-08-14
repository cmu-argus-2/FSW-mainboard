from core import logger


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

    def debug(self, msg, exc=None):
        """
        Print a debug message formatted with the task name, filename, and line number

        :param msg: Debug message to print
        :param level: > 1 will print as a sub-level
        """
        if exc is not None:
            tb = exc.__traceback__
            while tb.tb_next:  # Iterate to the last traceback
                tb = tb.tb_next
            lineno = tb.tb_lineno
            filename = tb.tb_frame.f_code.co_filename

            # Extract just the filename without the full path
            filename = filename.split("/")[-1]

            # Print the message in the desired format
            print(f"[{self.ID}][{self.name}][{filename}:{lineno}] {msg}")
        else:
            # If no exception is provided, just print the message
            print(f"[{self.ID}][{self.name}] {msg}")

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
            self.debug(f"{e}", exc=e)

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
