import os
import sys

# Add the emulator/cp directory to the path
emulator_dir = os.path.dirname(os.path.abspath(__file__))
cp_dir = os.path.join(emulator_dir, "cp")
sys.path.insert(0, cp_dir)

sys.modules["micropython"] = __import__("micropython_mock")
sys.modules["ulab"] = __import__("ulab_mock")
sys.modules["rtc"] = __import__("rtc_mock")
sys.modules["gc"] = __import__("gc_mock")
sys.modules["microcontroller"] = __import__("microcontroller_mock")
sys.modules["supervisor"] = __import__("supervisor_mock")
