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

_IDX_LENGTH = class_length(HAL_IDX)
_REGULAR_REBOOT_TIME = 60 * 60 * 24  # 24 hours
_PERIPH_REBOOT_COUNT_IDX = getattr(HAL_IDX, "PERIPH_REBOOT_COUNT")
_HAL_IDX_INV = {v: k for k, v in HAL_IDX.__dict__.items()}


class Task(TemplateTask):
    def __init__(self, id):
        super().__init__(id)
        self.name = "HAL_MONITOR"
        self.log_name = "hal"
        self.restored = False
        self.peripheral_reboot_count = 0

    ######################## HELPER FUNCTIONS ########################

    def idx_to_hal_name(self, idx: int):
        """Return the HAL_IDX field name for a given index, or None if not found."""
        return _HAL_IDX_INV.get(idx)

    def close_data_process(self):
        for data_process in DH.get_all_data_processes():
            data_process.close()

    ######################## ERROR HANDLING ########################

    def error_decision(self, device_name, device_errors):
        # decide what to do with the error based, decision made on the most severe error
        if Errors.DEVICE_NOT_INITIALISED in device_errors:
            return [SATELLITE.handle_error(device_name), Errors.DEVICE_NOT_INITIALISED]
        elif Errors.IMU_FATAL_ERROR in device_errors:
            return [SATELLITE.handle_error(device_name), Errors.IMU_FATAL_ERROR]
        elif Errors.RADIO_RC64K_CALIBRATION_FAILED in device_errors:
            return [SATELLITE.handle_error(device_name), Errors.RADIO_RC64K_CALIBRATION_FAILED]
        elif Errors.RADIO_RC13M_CALIBRATION_FAILED in device_errors:
            return [SATELLITE.handle_error(device_name), Errors.RADIO_RC13M_CALIBRATION_FAILED]
        elif Errors.RADIO_PLL_CALIBRATION_FAILED in device_errors:
            return [SATELLITE.handle_error(device_name), Errors.RADIO_PLL_CALIBRATION_FAILED]
        elif Errors.RADIO_ADC_CALIBRATION_FAILED in device_errors:
            return [SATELLITE.handle_error(device_name), Errors.RADIO_ADC_CALIBRATION_FAILED]
        elif Errors.RADIO_IMG_CALIBRATION_FAILED in device_errors:
            return [SATELLITE.handle_error(device_name), Errors.RADIO_IMG_CALIBRATION_FAILED]
        elif Errors.RADIO_XOSC_START_FAILED in device_errors:
            return [SATELLITE.handle_error(device_name), Errors.RADIO_XOSC_START_FAILED]
        elif Errors.RADIO_PA_RAMPING_FAILED in device_errors:
            return [SATELLITE.handle_error(device_name), Errors.RADIO_PA_RAMPING_FAILED]

        return [Errors.NO_ERROR, Errors.NO_ERROR]

    def log_device_status(self, log_data):
        for device_name, error_list in SATELLITE.DEVICES_STATUS.items():
            error_idx = getattr(HAL_IDX, f"{device_name}_ERROR")
            error_count_idx = getattr(HAL_IDX, f"{device_name}_ERROR_COUNT")
            dead_idx = getattr(HAL_IDX, f"{device_name}_DEAD")
            log_data[error_idx] = error_list[0]
            log_data[error_count_idx] = error_list[1]
            log_data[dead_idx] = error_list[2]
        log_data[_PERIPH_REBOOT_COUNT_IDX] = self.peripheral_reboot_count
        return log_data

    def log_error_handle_info(self, results, device_name):
        result, device_error = results
        if result == Errors.NO_REBOOT:
            self.log_info(f"Device {device_name} has {device_error}, no reboot occured")
            SATELLITE.update_device_error(device_name, device_error)
        elif result == Errors.REBOOT_DEVICE:
            self.log_info(f"Rebooted {device_name} due to error {device_error}")
        elif result == Errors.GRACEFUL_REBOOT:
            self.peripheral_reboot_count += 1
            DH.graceful_shutdown()
            SATELLITE.graceful_reboot_devices(device_name)
            DH.restore_data_process_files()
            self.log_info(f"Gracefully rebooted {device_name} due to error {device_error}")
        elif result == Errors.DEVICE_DEAD:
            self.log_critical(f"Device {device_name} is dead")
        elif result == Errors.INVALID_DEVICE_NAME:
            self.log_error(f"Invalid device name {device_name}")

    async def main_task(self):
        log_data = [0] * _IDX_LENGTH
        log_data[HAL_IDX.TIME_HAL] = TPM.time()

        if SM.current_state == STATES.STARTUP:
            if not DH.data_process_exists(self.name):
                data_format = "L" + "B" * (_IDX_LENGTH - 1)
                DH.register_data_process(self.log_name, data_format, True, data_limit=10000)
            if not self.restored:
                prev_data = DH.data_process_registry[self.log_name].get_latest_data()
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
                                SATELLITE.update_device_dead(key_name.replace("_DEAD", ""), bool(value))
                                self.log_info(f"Restored {key_name} to {value}")
                            elif "PERIPH_REBOOT_COUNT" in key_name:
                                self.peripheral_reboot_count = value
                                self.log_info(f"Restored {key_name} to {value}")
                            else:
                                self.log_error(f"Unable to parse {key_name}")
                else:
                    self.log_info("Could not restore data process, starting fresh")
                self.restored = True

        for device_name, device_error_list in SATELLITE.SAMPLE_DEVICE_ERRORS.items():
            self.log_error_handle_info(self.error_decision(device_name, device_error_list), device_name)

        DH.log_data(self.log_name, self.log_device_status(log_data))
        # regular reboot every 24 hours
        if TPM.monotonic() - SATELLITE.BOOTTIME >= _REGULAR_REBOOT_TIME:
            # TODO: graceful shutdown for payload if needed
            DH.graceful_shutdown()
            SATELLITE.reboot()
