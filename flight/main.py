import gc
import sys
import time

from core import logger, setup_logger, state_manager
from hal.configuration import SATELLITE


# Memory stats
def print_memory_stats(call_gc=True):
    if call_gc:
        gc.collect()
    print(f"Memory stats after gc: {call_gc}")
    print(f"Total memory: {str(gc.mem_alloc() + gc.mem_free())} bytes")
    print(f"Memory free: {str(gc.mem_free())} bytes")
    print(f"Memory free: {int((gc.mem_alloc() / (gc.mem_alloc() + gc.mem_free())) * 100)}%")


print_memory_stats(call_gc=True)

for path in ["/hal", "/apps", "/core"]:
    if path not in sys.path:
        sys.path.append(path)

setup_logger(level="INFO")

print_memory_stats(call_gc=True)

print("Booting ARGUS-1...")
boot_errors = SATELLITE.boot_sequence()
print("ARGUS-1 booted.")
print(f"Boot Errors: {boot_errors}")


print("Waiting 1 sec...")
time.sleep(1)


print_memory_stats(call_gc=True)
# time.sleep(5000)

"""print("Running system diagnostics...")
errors = SATELLITE.run_system_diagnostics()
print("System diagnostics complete")
print("Errors:", errors)
"""

print_memory_stats(call_gc=False)
print_memory_stats(call_gc=True)

try:
    # Run forever

    from core import DataHandler as DH

    DH.delete_all_files()

    logger.info("Starting state manager")
    state_manager.start()

except Exception as e:
    logger.critical("ERROR:", e)
    # TODO Log the error
