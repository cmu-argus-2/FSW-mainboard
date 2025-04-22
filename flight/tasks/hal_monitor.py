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

_HAL_IDX_INV = {v: k for k, v in HAL_IDX.__dict__.items()}


class Task(TemplateTask):
    def __init__(self, id):
        super().__init__(id)
        self.name = "HAL_MONITOR"
        self.restored = False

    def idx_to_hal_name(self, idx: int):
        """Return the HAL_IDX field name for a given index, or None if not found."""
        return _HAL_IDX_INV.get(idx)

    def error_decision(self, device_name, device_error):
        if device_error == Errors.DEVICE_NOT_INITIALISED:
            return SATELLITE.handle_error(device_name)

    def log_device_status(self, log_data):
        for device_name, error_list in SATELLITE.DEVICES_STATUS.items():
            error_idx = getattr(HAL_IDX, f"{device_name}_ERROR")
            error_count_idx = getattr(HAL_IDX, f"{device_name}_ERROR_COUNT")
            dead_idx = getattr(HAL_IDX, f"{device_name}_DEAD")
            log_data[error_idx] = error_list[0]
            log_data[error_count_idx] = error_list[1]
            log_data[dead_idx] = error_list[2]
        return log_data

    async def main_task(self):
        log_data = [0] * IDX_LENGTH
        log_data[HAL_IDX.TIME_HAL] = TPM.time()

        if SM.current_state == STATES.STARTUP:
            if not DH.data_process_exists(self.name):
                data_format = "L" + "B" * (IDX_LENGTH - 1)
                DH.register_data_process(self.name, data_format, True, data_limit=10000)
                self.restored = True
            elif not self.restored:
                prev_data = DH.data_process_registry[self.name].get_latest_data()
                if prev_data is not None:
                    for idx, value in enumerate(prev_data):
                        if idx == HAL_IDX.TIME_HAL:
                            continue
                        else:
                            key_name = self.idx_to_hal_name(idx)
                            if "_ERROR_COUNT" in key_name:
                                SATELLITE.update_device_error_count(key_name.replace("_ERROR_COUNT", ""), value)
                                self.log_info(f"Restored {key_name} to {value}")
                            elif "_ERROR" in key_name:
                                pass
                            elif "_DEAD" in key_name:
                                SATELLITE.update_device_dead(key_name.replace("_DEAD", ""), value)
                                self.log_info(f"Restored {key_name} to {value}")
                            else:
                                self.log_error(f"Unable to parse {key_name}")
                    self.restored = True
            for device_name, device_error in SATELLITE.ERRORS.items():
                self.error_decision(device_name, device_error)

        else:
            for device_name, device_error_list in SATELLITE.SAMPLE_DEVICE_ERRORS.items():
                for device_error in device_error_list:
                    result = self.error_decision(device_name, device_error)
                    if result == Errors.NO_REBOOT:
                        SATELLITE.update_device_error(device_name, device_error)
                    elif result == Errors.REBOOT_DEVICE:
                        self.log_info(f"Rebooting {device_name} due to error {device_error}")
                    elif result == Errors.DEVICE_DEAD:
                        self.log_critical(f"Device {device_name} is dead")
                    elif result == Errors.INVALID_DEVICE_NAME:
                        self.log_error(f"Invalid device name {device_name}")

        DH.log_data(self.name, self.log_device_status(log_data))
        # regular reboot every 24 hours
        if TPM.monotonic() - SATELLITE.BOOTTIME >= REGULAR_REBOOT_TIME:
            # TODO: implement graceful shutdown
            SATELLITE.reboot()
