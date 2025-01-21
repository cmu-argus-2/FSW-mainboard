import time

import core.scheduler as scheduler
from core import logger
from core.states import STATES


class StateManager:
    """Singleton Class"""

    _instance = None

    __slots__ = (
        "__current_state",
        "__scheduled_tasks",
        "__initialized",
        "__task_config",
        "__states",
        "__tasks",
        "__previous_state",
        "__time_since_last_state_change",
    )

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):

        self.__current_state = None
        self.__scheduled_tasks = {}
        self.__initialized = False
        self.__task_config = None
        self.__tasks = {}
        self.__time_since_last_state_change = 0

    @property
    def current_state(self):
        return self.__current_state

    @property
    def scheduled_tasks(self):
        return self.__scheduled_tasks

    @property
    def time_since_last_state_change(self):
        return time.monotonic() - self.__time_since_last_state_change

    def start(self, start_state=STATES.STARTUP):
        """Starts the state machine

        Args:
        :param start_state: The state to start the state machine in
        :type start_state: STATES
        """

        from core.task_configuration import TASK_CONFIG

        self.__task_config = TASK_CONFIG
        self.__states = [STATES.STARTUP, STATES.DETUMBLING, STATES.NOMINAL, STATES.PAYLOAD, STATES.LOW_POWER]

        # init task objects
        for task_id, task_params in self.__task_config.items():
            self.__tasks[task_id] = task_params["Task"](task_id)

        self.__current_state = start_state

        self.__time_since_last_state_change = time.monotonic()
        self.switch_to(start_state)
        scheduler.run()

    def switch_to(self, new_state_id: int):
        """Switches to a new state and schedules the tasks if the state machine was not initialized

        Args:
        :param new_state: The name of the state to switch to
        :type new_state_id: id
        """

        if new_state_id not in self.__states:
            logger.critical(f"State {new_state_id} is not in the list of states")
            raise ValueError(f"State {new_state_id} is not in the list of states")

        if self.__initialized:
            # prevent illegal transitions
            if not (new_state_id in STATES.TRANSITIONS[self.__current_state]):
                logger.critical(f"No transition from {self.__current_state} to {new_state_id}")
                raise ValueError(f"No transition from {self.__current_state} to {new_state_id}")
        else:
            self.schedule_tasks()
            self.__initialized = True

        self.__previous_state = self.__current_state
        self.__current_state = new_state_id
        self.__time_since_last_state_change = time.monotonic()
        logger.info(f"Switched to state {new_state_id}")

    def schedule_tasks(self):
        self.__scheduled_tasks = {}  # Reset

        for task_id, task_params in self.__task_config.items():

            if "ScheduleLater" in task_params:
                schedule = scheduler.schedule_later
            else:
                schedule = scheduler.schedule

            frequency = task_params["Frequency"]
            priority = task_params["Priority"]
            task_fn = self.__tasks[task_id]._run
            self.__tasks[task_id].set_frequency(frequency)

            self.__scheduled_tasks[task_id] = schedule(frequency, task_fn, priority)

    def stop_all_tasks(self):
        for name, task in self.__scheduled_tasks.items():
            task.stop()

    def restart(self):
        """Restarts the state machine"""
        self.stop_all_tasks()
        self.start()

    def print_current_tasks(self):
        """Prints all current tasks being executed"""
        for task_name in self.__scheduled_tasks:
            print(task_name)

    def change_task_frequency(self, task_id, freq_hz):
        """Changes the frequency of a task"""
        self.__scheduled_tasks[task_id].change_rate(freq_hz)
        logger.info(f"Task {task_id} frequency changed to {freq_hz}")
