from hal.cubesat import CubeSat
from micropython import const

PYCUBED_V05 = const(0)
ARGUS_V1 = const(1)

# HARDWARE_VERSION = PYCUBED_V05
HARDWARE_VERSION = ARGUS_V1

# Enable for Middleware
DEBUG_MODE = False
EN_MIDDLEWARE = False

SATELLITE = None

if HARDWARE_VERSION == PYCUBED_V05:
    from hal.pycubed import PyCubed

    SATELLITE = PyCubed()
elif HARDWARE_VERSION == ARGUS_V1:
    from hal.argus_v1 import ArgusV1

    SATELLITE = ArgusV1(enable_middleware=EN_MIDDLEWARE, debug=DEBUG_MODE)
else:
    raise ValueError(f"Invalid hardware version {HARDWARE_VERSION}")
