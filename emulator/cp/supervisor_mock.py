import os
import sys


class _RuntimeMock:
    def __init__(self):
        self.autoreload = False


runtime = _RuntimeMock()


def reload():
    """Mock function for supervisor.reload(). Restarts the current script."""
    try:
        # Re-execute the current script with the full path to the Python executable
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        print(f"Error during reload: {e}")
