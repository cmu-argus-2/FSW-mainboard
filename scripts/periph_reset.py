import time

from hal.configuration import SATELLITE

print("Booting ARGUS...")
SATELLITE.boot_sequence()
print("ARGUS booted.")
print(f"Boot Errors: {SATELLITE.ERRORS}")

SATELLITE.print_device_list()
time.sleep(2)


def test_device(device_name, run_time=1):
    print(f"Testing {device_name}...")
    for _ in range(run_time):
        print(SATELLITE.handle_error(device_name))
    SATELLITE.print_device_list()


# ASIL 4 test
print("ASIL 4 test")
test_device("RADIO")
SATELLITE.print_device_list()

# ASIL 3 test
print("ASIL 3 test")
test_device("GPS", 2)
SATELLITE.print_device_list()

# ASIL 2 test
print("ASIL 2 test")
test_device("FUEL_GAUGE", 3)
SATELLITE.print_device_list()

# ASIL 1 test
print("ASIL 1 test")
test_device("BOARD_PWR", 5)

# Dead test
print("Dead test")
test_device("BOARD_PWR", 6)
