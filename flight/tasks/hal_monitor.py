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
from hal.drivers.errors import Error

IDX_LENGTH = class_length(HAL_IDX)


class Task(TemplateTask):
    def __init__(self, id):
        super().__init__(id)
        self.name = "HAL_MONITOR"

    def sample_error_list(self, errors):
        for device_name, device_error in errors.items():
            if device_error == Error.DEVICE_NOT_INITIALISED:
                SATELLITE.handle_error(device_name)

    def log_device_status(self):
        for device_name, error_list in SATELLITE.DEVICES_STATUS:
            error_idx = getattr(HAL_IDX, f"{device_name}_ERROR")
            error_count_idx = getattr(HAL_IDX, f"{device_name}_ERROR_COUNT")
            dead_idx = getattr(HAL_IDX, f"{device_name}_DEAD")
            self.log_data[error_idx] = error_list[0]
            self.log_data[error_count_idx] = error_list[1]
            self.log_data[dead_idx] = error_list[2]

    async def main_task(self):
        errors = SATELLITE.ERRORS
        self.log_data[HAL_IDX.TIME_HAL] = TPM.time()

        if not DH.data_process_exists("hal_monitor"):
            data_format = "L" + "B" * 3 * IDX_LENGTH
            DH.register_data_process("hal_monitor", data_format, True, data_limit=10000)

        if SM.current_state == STATES.STARTUP:
            self.sample_error_list(errors)
            self.log_device_status()
        else:
            pass
