import gc
import sys

from core import state_manager
from hal.configuration import SATELLITE
from sm_configuration import SM_CONFIGURATION, TASK_REGISTRY

for path in ["/hal", "/apps", "/core"]:
    if path not in sys.path:
        sys.path.append(path)

gc.collect()
print(str(gc.mem_free()) + " bytes free")

print("Booting ARGUS-1...")
boot_errors = SATELLITE.boot_sequence()
print("ARGUS-1 booted.")
print()

print("Boot Errors: ", boot_errors)
print()

"""print("Running system diagnostics...")
errors = SATELLITE.run_system_diagnostics()
print("System diagnostics complete")
print("Errors:", errors)
print()"""

"""
from apps.data_handler import DataHandler as DH
DH.delete_all_files()
"""

gc.collect()
print(str(gc.mem_free()) + " bytes free")


try:
    # Run forever
    state_manager.start("STARTUP", SM_CONFIGURATION, TASK_REGISTRY)

except Exception as e:
    print("ERROR:", e)
    # TODO Log the error
