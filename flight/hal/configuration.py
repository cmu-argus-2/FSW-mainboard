import supervisor
from hal.cubesat import CubeSat

supervisor.runtime.autoreload = False

DEBUG_MODE = False

SATELLITE: CubeSat = None


from hal.argus_v4 import ArgusV4  # noqa: E402

SATELLITE = ArgusV4(debug=DEBUG_MODE)
