import sys

sys.path.append("./lib/hal/cp/")
sys.modules["micropython"] = __import__("micropython_mock")
sys.modules["ulab"] = __import__("ulab_mock")
sys.modules["rtc"] = __import__("rtc_mock")
sys.modules["gc"] = __import__("gc_mock")
sys.modules["microcontroller"] = __import__("microcontroller_mock")
