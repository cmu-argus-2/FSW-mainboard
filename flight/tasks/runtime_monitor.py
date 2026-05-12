"""Task runtime monitor.

Periodically prints cumulative timing statistics for each scheduled task.
"""

from core import TemplateTask
from core import state_manager as SM
from core.states import TASK, STATES

_TASK_NAMES = {value: name for name, value in TASK.__dict__.items() if not name.startswith("__")}


def _format_ms_from_ns(value_ns):
    return "{:.2f}ms".format(value_ns / 1000000)


class Task(TemplateTask):
    def __init__(self, id):
        super().__init__(id)
        self.name = "RUNTIME_MONITOR"

    def _task_label(self, task_id, stats):
        if stats is not None and stats.get("name"):
            return stats["name"]
        return _TASK_NAMES.get(task_id, "TASK_{}".format(task_id))

    async def main_task(self):
        # Skip reporting during startup
        if SM.current_state == STATES.STARTUP:
            return

        scheduled_tasks = SM.scheduled_tasks
        if not scheduled_tasks:
            print("No scheduled tasks to report yet")
            return

        print("Task runtime statistics (cumulative since boot)")
        for task_id in sorted(scheduled_tasks):
            stats = self.get_runtime_stat(task_id)
            task_name = self._task_label(task_id, stats)
            if stats is None or stats["count"] == 0:
                print("  {}: no samples yet".format(task_name))
                continue

            avg_ns = stats["total_ns"] // stats["count"]
            print(
                "  {}: avg={} min={} max={} samples={}".format(
                    task_name,
                    _format_ms_from_ns(avg_ns),
                    _format_ms_from_ns(stats["min_ns"]),
                    _format_ms_from_ns(stats["max_ns"]),
                    stats["count"],
                )
            )