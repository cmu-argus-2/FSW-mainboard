# HAL Monitor Task
# This task is responsible for monitoring the health of the hardware abstraction layer (HAL),
# performing diagnostics in case of failure, and reporting/logging HAL status.

from apps.telemetry.constants import HAL_IDX, class_length
from core import DataHandler as DH
from core import TemplateTask
from core import state_manager as SM
from core.states import STATES
from core.time_processor import TimeProcessor as TPM
from hal.configuration import SATELLITE
from hal.drivers.errors import Errors

IDX_LENGTH = class_length(HAL_IDX)
REGULAR_REBOOT_TIME = 60 * 60 * 24  # 24 hours


class Task(TemplateTask):
    def __init__(self, id):
        super().__init__(id)
        self.name = "HAL_MONITOR"

    def error_decision(self, device_name, device_error):
        if device_error == Errors.DEVICE_NOT_INITIALISED:
            return SATELLITE.handle_error(device_name)

    def log_device_status(self):
        for device_name, error_list in SATELLITE.DEVICES_STATUS:
            error_idx = getattr(HAL_IDX, f"{device_name}_ERROR")
            error_count_idx = getattr(HAL_IDX, f"{device_name}_ERROR_COUNT")
            dead_idx = getattr(HAL_IDX, f"{device_name}_DEAD")
            self.log_data[error_idx] = error_list[0]
            self.log_data[error_count_idx] = error_list[1]
            self.log_data[dead_idx] = error_list[2]

    async def main_task(self):
        self.log_data[HAL_IDX.TIME_HAL] = TPM.time()

        if SM.current_state == STATES.STARTUP:
            if not DH.data_process_exists("hal_monitor"):
                data_format = "L" + "B" * 3 * IDX_LENGTH
                DH.register_data_process("hal_monitor", data_format, True, data_limit=10000)
            else:
                # restore last startup data
                pass
            for device_name, device_error in SATELLITE.ERRORS.items():
                self.error_decision(device_name, device_error)
        else:
            for device_name, device_error_list in SATELLITE.SAMPLE_DEVICE_ERRORS.items():
                for device_error in device_error_list:
                    result = self.error_decision(device_name, device_error)
                    if result == Errors.NO_REBOOT:
                        SATELLITE.update_device_error(device_name, device_error)

        self.log_device_status()

        # regular reboot every 24 hours
        if TPM.monotonic - SATELLITE.BOOTTIME >= REGULAR_REBOOT_TIME:
            # TODO: implement graceful shutdown
            SATELLITE.reboot()
