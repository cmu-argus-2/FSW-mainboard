"""
Core Scheduler Module for Argus. This module provides a simple event loop for running a set of concurrent tasks.
Each task is a coroutine, implemented as a generator in CircuitPython. The scheduler manages the execution of tasks,
scheduling, sleeping, and task prioritization.

Example Usage:
    async def application_loop():
        pass

    def run():
        loop = Loop()
        loop.schedule(100, application_loop)
        loop.run()

    if __name__ == '__main__':
        run()
"""

import time

# Set up a monotonic clock is used to avoid issues with system clock adjustments.
_monotonic_ns = time.monotonic_ns  # nanoseconds


def _yield_once():
    """
    This provides a way for a coroutine to yield control back to the event loop.
    Returns an object whose __await__ method yields once. When awaited, it suspends
    the coroutine and yield the processor, allowing other tasks to run.
    """

    class _CallMeNextTime:
        def __await__(self):
            """This is inside the scheduler where we know generator yield is the
            implementation of task switching in CircuitPython. This throws
            control back out through user code and up to the scheduler's
            __iter__ stack which will see that we've suspended _current."""
            yield

    return _CallMeNextTime()


def _get_future_nanos(seconds_in_future):
    """Calculates a future timestamp in nanoseconds, given a delay in seconds."""
    return _monotonic_ns() + int(seconds_in_future * 1000000000)


class PriorityTask:
    """Represents an asynchronous task with a priority."""

    def __init__(self, coroutine, priority: int):
        self.coroutine = coroutine  # the coroutine to be executed
        self.priority = priority  # integer representing the priority (lower is higher priority)

    def priority_sort(self):
        return self.priority

    def __repr__(self):
        return "{{Task {}, Priority {}}}".format(self.coroutine, self.priority)

    __str__ = __repr__


class Sleeper:
    """
    Represents a task that is sleeping until a specific time.
    When a task calls sleep, it is wrapped in a Sleeper and added to the event loop's
    sleeping list.
    """

    def __init__(self, resume_nanos: int, task: PriorityTask):
        self.task = task
        self._resume_nanos = resume_nanos  # The timestamp when the task should resume

    def resume_nanos(self):
        return self._resume_nanos  # The timestamp when the task should resume

    def priority_sort(self):
        return self.task.priority

    def __repr__(self):
        return "{{Sleeper remaining: {:.2f}, task: {} }}".format((self.resume_nanos() - _monotonic_ns()), self.task)

    __str__ = __repr__


class ScheduledTask:
    """Manages tasks that should run at a fixed frequency."""

    def __init__(
        self,
        loop,
        hz,
        forward_async_fn,
        priority,
        forward_args,
        forward_kwargs,
    ):
        # reference to the event loop
        self._loop = loop
        # coroutine function to run
        self._forward_async_fn = forward_async_fn
        self._forward_args = forward_args
        self._forward_kwargs = forward_kwargs
        # time between invocations
        self._nanoseconds_per_invocation = (1 / hz) * 1000000000
        # control flags
        self._stop = False
        self._running = False
        self._scheduled_to_run = False
        # priority
        self._priority = priority

    def change_rate(self, hz: float):
        """Update the task rate to a new frequency."""
        self._nanoseconds_per_invocation = (1 / hz) * 1000000000

    def stop(self):
        """Stop the task (does not interrupt a currently running task."""
        self._stop = True

    def start(self):
        """Schedule the task if not already scheduled."""
        self._stop = False
        if not self._scheduled_to_run:  # Check if the task is already scheduled to run
            self._loop.add_task(self._run_at_fixed_rate(), self._priority)

    async def _run_at_fixed_rate(self):
        """Coroutine that runs the task at the specified rate."""
        self._scheduled_to_run = True
        try:
            target_run_nanos = _monotonic_ns()
            while True:
                if self._stop:
                    return

                iteration = self._forward_async_fn(*self._forward_args, **self._forward_kwargs)

                self._running = True
                try:
                    await iteration
                finally:
                    self._running = False

                if self._stop:
                    return  # Check before waiting

                # Try to reschedule for the next window without skew. If we're falling behind,
                # just go as fast as possible & schedule to run "now." If we catch back up again
                # we'll return to seconds_per_invocation without doing a bunch of catchup runs.
                target_run_nanos = target_run_nanos + self._nanoseconds_per_invocation
                # print('target_run_nanos is ', target_run_nanos)
                now_nanos = _monotonic_ns()
                if now_nanos <= target_run_nanos:
                    await self._loop._sleep_until_nanos(target_run_nanos)
                else:
                    target_run_nanos = now_nanos
                    # Allow other tasks a chance to run if this task is too slow.
                    await _yield_once()
        finally:
            self._scheduled_to_run = False

    def __repr__(self):
        hz = 1 / (self._nanoseconds_per_invocation / 1000000000)
        state = "running" if self._running else "waiting"
        return "{{ScheduledTask {} rate: {}hz, fn: {}}}".format(state, hz, self._forward_async_fn)

    __str__ = __repr__


class Scheduler:
    """
    Core event loop class.  Manages the execution of tasks, handling scheduling,
    sleeping, and task prioritization. With run(), it manages your main application loop.
    """

    def __init__(self, debug=False):
        self._tasks = []  # list of active PriorityTask instances
        self._sleeping = []  # List of Sleeper instances
        self._ready = []  # List of sleeping tasks ready to resume
        self._current = None  # The current task being executed
        self._debug = debug  # Debug flag

    @property
    def debug(self):
        return self._debug

    def enable_debug_logging(self):
        self._debug = True

    def add_task(self, awaitable_task, priority):
        """
        Add a concurrent task (known as a coroutine, implemented as a generator in CircuitPython)
        Use:
          scheduler.add_task( my_async_method() )
        :param awaitable_task:  The coroutine to be concurrently driven to completion.
        """
        self._tasks.append(PriorityTask(awaitable_task, priority))

    async def sleep(self, seconds):
        """
        From within a coroutine, this suspends your call stack for some amount of time.
        NOTE: Always`await`this! IT will wait at least 'seconds' long to call your task again.
        """
        await self._sleep_until_nanos(_get_future_nanos(seconds))

    def run_later(self, seconds_to_delay, awaitable_task, priority):
        """
        Add a concurrent task, delayed by some seconds.
        Use:
          scheduler.run_later( seconds_to_delay=1.2, my_async_method() )
        :param seconds_to_delay: How long until the task should be kicked off?
        :param awaitable_task:   The coroutine to be concurrently driven to completion.
        """
        start_nanos = _get_future_nanos(seconds_to_delay)

        async def _run_later():
            await self._sleep_until_nanos(start_nanos)
            await awaitable_task

        self.add_task(_run_later(), priority)

    def schedule(self, hz: float, coroutine_function, priority, *args, **kwargs):
        """
        Schedule a coroutine to run at a specified frequency.

        The event loop will call the coroutine at the specified `hz` rate.
        Only one instance of the coroutine will run at a time. Uses `sleep()`
        to yield control when idle, minimizing CPU usage.

        Example:
        async def main_loop():
            await your_code()
        scheduled_task = get_loop().schedule(hz=100, coroutine_function=main_loop)
        get_loop().run()

        :param hz: Frequency in Hz at which to run the coroutine.
        :param coroutine_function: The coroutine to schedule.
        """
        assert coroutine_function is not None, "coroutine function must not be none"
        task = ScheduledTask(self, hz, coroutine_function, priority, args, kwargs)
        task.start()
        return task

    def schedule_later(self, hz: float, coroutine_function, priority, *args, **kwargs):
        """
        Schedule a coroutine to start after an initial delay of one interval.

        Runs `coroutine_function` after the first `hz` interval and then continues
        at the specified rate.

        :param hz: Frequency in Hz at which to run the coroutine after the initial delay.
        :param coroutine_function: The coroutine to schedule.
        """
        ran_once = False

        async def call_later():
            nonlocal ran_once
            if ran_once:
                await coroutine_function(*args, **kwargs)
            else:
                await _yield_once()
                ran_once = True

        return self.schedule(hz, call_later, priority)

    def run(self):
        """
        Example Usage:
            async def application_loop():
                pass

            def run():
                loop = Loop()
                loop.schedule(100, application_loop)
                loop.run()

            if __name__ == '__main__':
                run()

        Note:
        - StopIteration ends a coroutine in CircuitPython.
        - Any other exception stops the loop and shows a stack trace.
        """

        assert self._current is None, "Loop can only be advanced by 1 stack frame at a time."

        self._loopnum = 0
        while self._tasks or self._sleeping:
            if self._debug:
                print("[{}] ---- sleeping: {}, active: {}\n".format(self._loopnum, len(self._sleeping), len(self._tasks)))

            self._step()
            self._loopnum += 1

        if self._debug:
            print("Loop completed", self._tasks, self._sleeping)

    def _step(self):
        """
        Executes one iteration of the event loop, managing tasks and sleep states.
        In order:
        - Sorts active tasks by priority and executes them.
        - Populates and sorts the "ready" list based on tasks that are due to run.
        - Runs ready tasks and removes them from the sleeping list.
        - If no active tasks remain, calculates sleep duration based on the earliest
        sleeping task's resume time and allows the system to sleep until the next task is due.
        """

        if self._debug:
            print("  stepping over ", len(self._tasks), " tasks")

        # Sort tasks by priority before running them
        self._tasks.sort(key=PriorityTask.priority_sort)

        # Run each task in the sorted list, removing it from _tasks after execution
        tasks_to_run = self._tasks[:]  # O(n) copy
        self._tasks.clear()  # O(1)

        for task in tasks_to_run:  # O(n) iteration
            self._run_task(task)

        if self._debug:
            print("  sleeping list (unsorted):")
            for i in self._sleeping:
                print("    {}".format(i))

        # Create the ready list by selecting tasks from _sleeping that are ready to run based on their resume time
        # Since _sleeping is kept sorted by resume time, we can optimize this
        now = _monotonic_ns()
        self._ready = []
        cutoff_index = 0

        for i, sleeper in enumerate(self._sleeping):
            if sleeper.resume_nanos() <= now:
                self._ready.append(sleeper)
                cutoff_index = i + 1
            else:
                break  # Since sorted, no need to check further

        # Sort the ready tasks by priority
        self._ready.sort(key=lambda x: x.task.priority)

        if self._debug:
            print("  ready list (sorted)")
            for i in self._ready:
                print("    {}".format(i))

        # Execute each ready task, removing it from both _ready and _sleeping lists after completion
        ready_tasks = self._ready[:]  # O(n) copy
        self._ready.clear()  # O(1)

        # Remove ready tasks from sleeping list efficiently since we know the cutoff index
        if cutoff_index > 0:
            self._sleeping = self._sleeping[cutoff_index:]  # O(n) slice, but only once

        for ready_task in ready_tasks:  # O(n) iteration
            self._run_task(ready_task.task)

        # If there are no more active tasks but there are tasks in the sleeping list, determine sleep duration
        if len(self._tasks) == 0 and len(self._sleeping) > 0:
            # _sleeping is already sorted by resume time, so first element is the earliest
            next_sleeper = self._sleeping[0]
            sleep_nanos = next_sleeper.resume_nanos() - _monotonic_ns()

            if sleep_nanos > 0:
                # Calculate sleep duration in seconds and put the system to sleep until the next task is due
                # This helps reduce CPU usage when there are no immediate tasks
                sleep_seconds = sleep_nanos / 1000000000.0

                if self._debug:
                    print("  No active tasks.  Sleeping for ", sleep_seconds, "s. \n", self._sleeping)

                time.sleep(sleep_seconds)

    def _run_task(self, task: PriorityTask):
        """
        Runs a task and re-queues for the next loop if it is both (1) not complete and (2) not sleeping.
        """
        self._current = task
        try:
            # Attempt to run the next step of the coroutine
            task.coroutine.send(None)

            if self._debug:
                print("  current", self._current)

            # If the task hasn’t suspended itself and remains active, add it back to the queue
            if self._current is not None:
                self._tasks.append(task)
        except StopIteration:
            pass  # Task is complete
        finally:
            self._current = None  # Clear the current task reference upon completion

    async def _sleep_until_nanos(self, target_run_nanos):
        """
        Suspends the current coroutine until the specified target time (`target_run_nanos` in nanoseconds).
        It adds the current task to the sleeping list until the target time is reached. then yields control,
        allowing the scheduler to resume this coroutine at the next execution cycle.

        Preconditions:
        - Must be called from within an active task, indicated by `self._current` being non-None.
        """

        assert self._current is not None, "You can only sleep from within a task"

        # Register the current task in the sleeping queue, maintaining sorted order by resume time
        sleeper = Sleeper(target_run_nanos, self._current)

        # Manual linear search insertion to maintain sorted order - O(n) search + O(n) insert
        insert_pos = len(self._sleeping)  # Default to insert at end
        for i, s in enumerate(self._sleeping):
            if s.resume_nanos() > target_run_nanos:
                insert_pos = i
                break
        self._sleeping.insert(insert_pos, sleeper)

        if self._debug:
            print("  sleeping ", self._current)

        # Clear the current task indicator to mark it as suspended
        self._current = None
        # Yield control back to the scheduler.
        await _yield_once()
