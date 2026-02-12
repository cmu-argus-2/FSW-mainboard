import os
import sys

import pytest


def add_project_root_to_path():
    project_root = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.abspath(os.path.join(project_root, ".."))

    # Add the project root to PYTHONPATH if it isn't already
    if project_root not in sys.path:
        sys.path.append(project_root)


if __name__ == "__main__":
    add_project_root_to_path()

    import numpy  # noqa: F401
    import tests.cp_mock  # noqa: F401

    sys.path.append("emulator/cp")
    sys.modules["micropython"] = __import__("micropython_mock")
    sys.modules["ulab"] = __import__("ulab_mock")

    # Run pytest (default: full tests folder). Allow pass-through args, e.g.
    # python3.10 tests/run_tests.py -q tests/test_cmd_processor.py
    pytest_args = sys.argv[1:] if len(sys.argv) > 1 else ["tests"]
    pytest.main(pytest_args)
