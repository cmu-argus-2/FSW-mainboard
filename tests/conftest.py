import os
import sys


def _ensure_path(path):
    if path not in sys.path:
        sys.path.append(path)


# Ensure repository root and emulator mocks are importable when running pytest directly.
_TESTS_DIR = os.path.abspath(os.path.dirname(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_TESTS_DIR, ".."))
_EMULATOR_CP = os.path.join(_REPO_ROOT, "emulator", "cp")
_FLIGHT_ROOT = os.path.join(_REPO_ROOT, "flight")

_ensure_path(_REPO_ROOT)
_ensure_path(_EMULATOR_CP)
_ensure_path(_FLIGHT_ROOT)

# Provide a minimal boot_out.txt expected by hal/configuration.py during imports.
_BOOT_OUT = os.path.join(_REPO_ROOT, "boot_out.txt")
if not os.path.exists(_BOOT_OUT):
    with open(_BOOT_OUT, "w", encoding="utf-8") as f:
        f.write("Adafruit CircuitPython\n")
        f.write("Board ID: Argus3\n")


# Register CircuitPython/MicroPython compatibility shims.
sys.modules.setdefault("micropython", __import__("micropython_mock"))
sys.modules.setdefault("ulab", __import__("ulab_mock"))
sys.modules.setdefault("supervisor", __import__("supervisor_mock"))

# Load broader CPython compatibility aliases used by flight imports.
import emulator.cp_mock  # noqa: F401, E402
