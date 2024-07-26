from hal.cubesat import CubeSat
from hal.emulator import satellite

# Enable for Middleware
DEBUG_MODE = True
EN_MIDDLEWARE = True
SOCKET_RADIO = True

SATELLITE: CubeSat = None
SATELLITE = satellite(enable_middleware=EN_MIDDLEWARE, debug=DEBUG_MODE, use_socket=SOCKET_RADIO)
