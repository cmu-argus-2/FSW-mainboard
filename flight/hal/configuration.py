import supervisor
from hal.cubesat import CubeSat
from micropython import const

supervisor.runtime.autoreload = False

with open("boot_out.txt") as boot:
    lines = boot.readlines()  # Read all lines into a list
    if len(lines) > 1:  # Check if the file has at least two lines
        second_line = lines[1].strip()  # Get the second line and strip whitespace
        board_id = second_line.split(":")[1].strip()  # Extract the part after the colon

DEBUG_MODE = False

SATELLITE: CubeSat = None

if board_id == "PyCubed":
    from hal.pycubed import PyCubed

    SATELLITE = PyCubed()

elif board_id == "argus1-j20":
    from hal.argus_v1 import ArgusV1

    SATELLITE = ArgusV1(debug=DEBUG_MODE)

elif board_id == "ArgusMain":
    from hal.argus_v1_1 import ArgusV1 as ArgusV1_1

    SATELLITE = ArgusV1_1(debug=DEBUG_MODE)

elif board_id == "Argus2":
    from hal.argus_v2 import ArgusV2

    SATELLITE = ArgusV2(debug=DEBUG_MODE)

elif board_id == "Argus3":
    from hal.argus_v3 import ArgusV3

    SATELLITE = ArgusV3(debug=DEBUG_MODE)

else:
    raise ValueError(f"Invalid hardware version {board_id}")
