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

    def __init__(self, coroutine, priority: int, urgent: bool = False):
        self.coroutine = coroutine  # the coroutine to be executed
        self.priority = priority  # integer representing the priority (lower is higher priority)
        self.urgent = urgent  # flag indicating if this task is urgent (like watchdog)

    def priority_sort(self):
        # Urgent tasks get even higher priority by subtracting 0.5
        return self.priority - 0.5 if self.urgent else self.priority

    def __repr__(self):
        urgent_str = " URGENT" if self.urgent else ""
        return "{{Task {}, Priority {}{}}}".format(self.coroutine, self.priority, urgent_str)

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
        return self.task.priority_sort()  # Use the task's priority_sort method to respect urgency

    def __repr__(self):
        return "{{Sleeper remaining: {:.2f}, task: {} }}".format(
            (self.resume_nanos() - _monotonic_ns()) / 1000000000.0, self.task
        )

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
        urgent=False,
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
        self._urgent = urgent

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
            self._loop.add_task(self._run_at_fixed_rate(), self._priority, self._urgent)

    async def _run_at_fixed_rate(self):
        """Coroutine that runs the task at the specified rate."""
        self._scheduled_to_run = True
        try:
            target_run_nanos = _monotonic_ns()
            while True:
                if self._stop:
                    return

                # Call the function - check if it needs arguments
                if self._forward_args or self._forward_kwargs:
                    iteration = self._forward_async_fn(*self._forward_args, **self._forward_kwargs)
                else:
                    iteration = self._forward_async_fn()

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
        self._preemption_check_interval = 5  # Check for preemption every N tasks

    @property
    def debug(self):
        return self._debug

    def enable_debug_logging(self):
        self._debug = True

    def add_task(self, awaitable_task, priority, urgent=False):
        """
        Add a concurrent task (known as a coroutine, implemented as a generator in CircuitPython)
        Use:
          scheduler.add_task( my_async_method() )
        :param awaitable_task:  The coroutine to be concurrently driven to completion.
        :param priority: Task priority (lower is higher priority)
        :param urgent: Flag indicating if this is an urgent task that can preempt others
        """
        self._tasks.append(PriorityTask(awaitable_task, priority, urgent))

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

    def schedule(self, hz: float, coroutine_function, priority, *args, urgent=False, **kwargs):
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
        :param priority: Task priority (lower is higher priority)
        :param urgent: Flag indicating if this is an urgent task that can preempt others
        """
        assert coroutine_function is not None, "coroutine function must not be none"
        task = ScheduledTask(self, hz, coroutine_function, priority, args, kwargs, urgent=urgent)
        task.start()
        return task

    def schedule_later(self, hz: float, coroutine_function, priority, *args, urgent=False, **kwargs):
        """
        Schedule a coroutine to start after an initial delay of one interval.

        Runs `coroutine_function` after the first `hz` interval and then continues
        at the specified rate.

        :param hz: Frequency in Hz at which to run the coroutine after the initial delay.
        :param coroutine_function: The coroutine to schedule.
        :param priority: Task priority (lower is higher priority)
        :param urgent: Flag indicating if this is an urgent task that can preempt others
        """
        ran_once = False

        async def call_later():
            nonlocal ran_once
            if ran_once:
                await coroutine_function(*args, **kwargs)
            else:
                await _yield_once()
                ran_once = True

        return self.schedule(hz, call_later, priority, urgent=urgent)

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

    def _get_urgent_ready_tasks(self):
        """Get urgent tasks that are ready to run immediately"""
        if not self._sleeping:
            return []

        now = _monotonic_ns()
        urgent_ready = []

        for sleeper in self._sleeping[:]:  # Create a copy to avoid modification during iteration
            if sleeper.resume_nanos() <= now and sleeper.task.urgent:
                urgent_ready.append(sleeper)

        return urgent_ready

    def _step(self):
        """
        Executes one iteration of the event loop, managing tasks and sleep states.
        Enhanced with proper preemptive scheduling for urgent tasks.
        """

        if self._debug:
            print("  stepping over ", len(self._tasks), " tasks")

        # PHASE 1: Handle urgent tasks that are ready to run immediately
        urgent_ready = self._get_urgent_ready_tasks()
        if urgent_ready:
            if self._debug:
                print(f"  Processing {len(urgent_ready)} urgent ready tasks")

            # Sort urgent tasks by priority
            urgent_ready.sort(key=lambda sleeper: sleeper.task.priority_sort())

            for urgent_sleeper in urgent_ready:
                if urgent_sleeper in self._sleeping:  # Double-check it's still there
                    self._sleeping.remove(urgent_sleeper)
                    self._run_task(urgent_sleeper.task)

        # PHASE 2: Process active tasks with preemption awareness
        if self._tasks:
            # Sort tasks by priority (urgent tasks naturally sort first)
            self._tasks.sort(key=lambda task: task.priority_sort())

            # Run tasks, checking for urgent preemption periodically
            tasks_to_run = self._tasks[:]
            self._tasks.clear()

            task_count = 0
            for task in tasks_to_run:
                self._run_task(task)
                task_count += 1

                # Check for urgent preemption every few tasks or after urgent/high-priority tasks
                if task_count % self._preemption_check_interval == 0 or task.urgent or task.priority <= 1:

                    urgent_ready = self._get_urgent_ready_tasks()
                    if urgent_ready:
                        if self._debug:
                            print(f"  Preempting after task {task_count} for urgent tasks")

                        urgent_ready.sort(key=lambda sleeper: sleeper.task.priority_sort())
                        for urgent_sleeper in urgent_ready:
                            if urgent_sleeper in self._sleeping:
                                self._sleeping.remove(urgent_sleeper)
                                self._run_task(urgent_sleeper.task)

        # PHASE 3: Handle normally scheduled sleeping tasks
        if self._sleeping:
            if self._debug:
                print("  sleeping list (unsorted):")
                for sleeper in self._sleeping:
                    print("    {}".format(sleeper))

            # Create the ready list by selecting tasks from _sleeping that are ready to run
            now = _monotonic_ns()
            ready_tasks = []
            remaining_sleeping = []

            for sleeper in self._sleeping:
                if sleeper.resume_nanos() <= now:
                    ready_tasks.append(sleeper)
                else:
                    remaining_sleeping.append(sleeper)

            self._sleeping = remaining_sleeping

            # Sort ready tasks by priority (urgent tasks first)
            ready_tasks.sort(key=lambda sleeper: sleeper.task.priority_sort())

            if self._debug and ready_tasks:
                print("  ready list (sorted by priority):")
                for sleeper in ready_tasks:
                    print("    {}".format(sleeper))

            # Execute ready tasks
            for sleeper in ready_tasks:
                self._run_task(sleeper.task)

        # PHASE 4: Sleep if no active tasks but sleeping tasks exist
        if len(self._tasks) == 0 and len(self._sleeping) > 0:
            # Sort sleeping tasks by resume time to find the earliest
            self._sleeping.sort(key=lambda sleeper: sleeper.resume_nanos())
            next_sleeper = self._sleeping[0]
            sleep_nanos = next_sleeper.resume_nanos() - _monotonic_ns()

            if sleep_nanos > 0:
                sleep_seconds = sleep_nanos / 1000000000.0

                if self._debug:
                    print("  No active tasks. Sleeping for {:.3f}s until next task".format(sleep_seconds))

                # For urgent tasks, sleep in smaller chunks to enable quick response
                min_urgent_priority = min((s.task.priority for s in self._sleeping if s.task.urgent), default=float("inf"))
                if min_urgent_priority <= 1:  # High-priority urgent tasks exist
                    sleep_seconds = min(sleep_seconds, 0.001)  # Max 1ms sleep for responsiveness

                time.sleep(sleep_seconds)

    def _run_task(self, task: PriorityTask):
        """
        Runs a task and re-queues for the next loop if it is both (1) not complete and (2) not sleeping.
        Enhanced with execution time monitoring for debugging.
        """
        self._current = task
        start_time = _monotonic_ns()

        try:
            # Attempt to run the next step of the coroutine
            task.coroutine.send(None)

            # Monitor execution time for debugging and starvation detection
            elapsed_ns = _monotonic_ns() - start_time
            elapsed_ms = elapsed_ns / 1000000

            if self._debug:
                priority_str = "URGENT" if task.urgent else f"P{task.priority}"
                print(f"  Task {priority_str} executed in {elapsed_ms:.2f}ms: {task.coroutine}")

            # Warn about long-running non-urgent tasks
            if not task.urgent and elapsed_ms > 10:  # 10ms threshold
                if self._debug:
                    print(f"  WARNING: Non-urgent task took {elapsed_ms:.1f}ms - may block urgent tasks")

            # If the task hasn't suspended itself and remains active, add it back to the queue
            if self._current is not None:
                self._tasks.append(task)

        except StopIteration:
            if self._debug:
                print(f"  Task completed: {task}")
        except Exception as e:
            # Handle other exceptions to prevent scheduler crash
            if self._debug:
                print(f"  Task {task} raised exception: {e}")
            # Don't re-queue task that threw an exception to prevent infinite error loops
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

        # Register the current task in the sleeping queue, set to resume at `target_run_nanos`
        self._sleeping.append(Sleeper(target_run_nanos, self._current))

        if self._debug:
            sleep_duration_ms = (target_run_nanos - _monotonic_ns()) / 1000000
            print(f"  Sleeping {self._current} for {sleep_duration_ms:.1f}ms")

        # Clear the current task indicator to mark it as suspended
        self._current = None
        # Yield control back to the scheduler.
        await _yield_once()
