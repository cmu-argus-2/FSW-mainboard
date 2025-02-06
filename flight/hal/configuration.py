from hal.cubesat import CubeSat
from micropython import const

PYCUBED_V05 = const(0)
ARGUS_V1 = const(1)
ARGUS_V1_1 = const(2)
ARGUS_V2 = const(3)

# HARDWARE_VERSION = PYCUBED_V05
# HARDWARE_VERSION = ARGUS_V1
HARDWARE_VERSION = ARGUS_V1_1
# HARDWARE_VERSION = ARGUS_V2

DEBUG_MODE = False

SATELLITE: CubeSat = None

if HARDWARE_VERSION == PYCUBED_V05:
    from hal.pycubed import PyCubed

    SATELLITE = PyCubed()

elif HARDWARE_VERSION == ARGUS_V1:
    from hal.argus_v1 import ArgusV1

    SATELLITE = ArgusV1(debug=DEBUG_MODE)

elif HARDWARE_VERSION == ARGUS_V1_1:
    from hal.argus_v1_1 import ArgusV1 as ArgusV1_1

    SATELLITE = ArgusV1_1(debug=DEBUG_MODE)

elif HARDWARE_VERSION == ARGUS_V2:
    from hal.argus_v2 import ArgusV2

    SATELLITE = ArgusV2(debug=DEBUG_MODE)

else:
    raise ValueError(f"Invalid hardware version {HARDWARE_VERSION}")
