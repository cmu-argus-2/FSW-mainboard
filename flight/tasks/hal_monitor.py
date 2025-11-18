# HAL Monitor Task
# This task is responsible for monitoring the health of the hardware abstraction layer (HAL).
# Every device in the HAL is monitored for errors, and if an error is detected, the task will
# decide what to do with the error based on the type of the error. Device status is logged
# to the data process, the task will log the error and reboot the device if necessary.
# The task also monitors the time since the last reboot and will reboot the system if it has been
# more than 24 hours since the last reboot.

from apps.telemetry.constants import HAL_IDX, class_length
from core import DataHandler as DH
from core import TemplateTask
from core import state_manager as SM
from core.satellite_config import hal_monitor_config as CONFIG
from core.states import STATES
from core.time_processor import TimeProcessor as TPM
from hal.configuration import SATELLITE
from hal.drivers.errors import Errors
from micropython import const

_IDX_LENGTH = class_length(HAL_IDX)
_REGULAR_REBOOT_TIME = CONFIG.REGULAR_REBOOT
_PERIPH_REBOOT_COUNT_IDX = getattr(HAL_IDX, "PERIPH_REBOOT_COUNT")
_HAL_IDX_INV = {v: k for k, v in HAL_IDX.__dict__.items()}
_GRACEFUL_REBOOT_INTERVAL = const(60 * 5)  # 1 minute interval, 5Hz task rate
_INDIVIDUAL_REBOOT_INTERVAL = const(10 * 5)  # 10 second interval, 5Hz task rate


class Task(TemplateTask):
    def __init__(self, id):
        super().__init__(id)
        self.name = "HAL_MONITOR"
        self.log_name = "hal"
        self.log_data = [0] * _IDX_LENGTH
        self.restored = False
        self.peripheral_reboot_count = 0
        self.graceful_reboot = False
        self.graceful_reboot_counter = 0
        self.turn_on_device = {}
        self.individual_reboot_counter = 0

    ######################## HELPER FUNCTIONS ########################

    def idx_to_hal_name(self, idx: int):
        """Return the HAL_IDX field name for a given index, or None if not found."""
        return _HAL_IDX_INV.get(idx)

    def close_data_process(self):
        if not DH.graceful_shutdown():
            self.log_info("Error during gracefully shutting down data process.")

    ######################## ERROR HANDLING ########################

    def error_decision(self, device_name, device_errors):
        # decide what to do with the error based, decision made on the most severe error
        if Errors.DEVICE_NOT_INITIALISED in device_errors:
            return [SATELLITE.handle_error(device_name), Errors.DEVICE_NOT_INITIALISED]
        elif Errors.FN_CALL_ERROR in device_errors:
            return [SATELLITE.handle_error(device_name), Errors.FN_CALL_ERROR]
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
        elif Errors.RTC_LOST_POWER in device_errors:
            return [Errors.LOG_DATA_ERROR, Errors.RTC_LOST_POWER]
        elif Errors.RTC_BATTERY_LOW in device_errors:
            return [Errors.LOG_DATA_ERROR, Errors.RTC_BATTERY_LOW]
        elif Errors.BATT_HEATER_EN_GPIO_ERROR in device_errors:
            return [Errors.LOG_DATA_ERROR, Errors.BATT_HEATER_EN_GPIO_ERROR]
        elif Errors.BATT_HEATER_HEAT0_GPIO_ERROR in device_errors:
            return [Errors.LOG_DATA_ERROR, Errors.BATT_HEATER_HEAT0_GPIO_ERROR]
        elif Errors.BATT_HEATER_HEAT1_GPIO_ERROR in device_errors:
            return [Errors.LOG_DATA_ERROR, Errors.BATT_HEATER_HEAT1_GPIO_ERROR]
        elif Errors.WATCHDOG_EN_GPIO_ERROR in device_errors:
            return [Errors.LOG_DATA_ERROR, Errors.WATCHDOG_EN_GPIO_ERROR]
        elif Errors.WATCHDOG_INPUT_GPIO_ERROR in device_errors:
            return [Errors.LOG_DATA_ERROR, Errors.WATCHDOG_INPUT_GPIO_ERROR]
        elif Errors.LIGHT_SENSOR_HIGHER_THAN_THRESHOLD in device_errors:
            return [Errors.LOG_DATA, Errors.LIGHT_SENSOR_HIGHER_THAN_THRESHOLD]
        elif Errors.LIGHT_SENSOR_LOWER_THAN_THRESHOLD in device_errors:
            return [Errors.LOG_DATA, Errors.LIGHT_SENSOR_LOWER_THAN_THRESHOLD]
        elif Errors.LIGHT_SENSOR_OVERFLOW in device_errors:
            return [Errors.LOG_DATA, Errors.LIGHT_SENSOR_OVERFLOW]

        return [Errors.NO_ERROR, Errors.NO_ERROR]

    def log_device_status(self):
        for device_name, error_list in SATELLITE.DEVICES_STATUS.items():
            error_idx = getattr(HAL_IDX, f"{device_name}_ERROR")
            error_count_idx = getattr(HAL_IDX, f"{device_name}_ERROR_COUNT")
            self.log_data[error_idx] = error_list[0]
            self.log_data[error_count_idx] = error_list[1]
        self.log_data[_PERIPH_REBOOT_COUNT_IDX] = self.peripheral_reboot_count

    def log_error_handle_info(self, results, device_name):
        result, device_error = results
        if result == Errors.NO_REBOOT:
            self.log_info(f"Device {device_name} has {device_error}, no reboot occured")
            SATELLITE.update_device_error(device_name, device_error)
        elif result == Errors.REBOOT_DEVICE:
            self.turn_on_device[device_name] = self.log_data[HAL_IDX.TIME_HAL]
            SATELLITE.update_device_error(device_name, device_error)
            self.log_info(f"Temporarily shut down {device_name} due to error {device_error}")
        elif result == Errors.GRACEFUL_REBOOT:
            SATELLITE.update_device_error(device_name, device_error)
            self.log_info(f"Queued graceful reboot for {device_name} due to error {device_error}")
            self.graceful_reboot = True
        elif result == Errors.DEVICE_DEAD:
            SATELLITE.update_device_error(device_name, result)
            self.log_critical(f"Device {device_name} is dead")
        elif result == Errors.LOG_DATA_ERROR:
            self.log_info(f"Device {device_name} has {device_error}, logging error")
            SATELLITE.update_device_error(device_name, device_error)
            SATELLITE.increment_device_error_count(device_name)
        elif result == Errors.LOG_DATA:
            self.log_info(f"Device {device_name} has {device_error}, logging data")
            SATELLITE.update_device_error(device_name, device_error)
        elif result == Errors.INVALID_DEVICE_NAME:
            self.log_error(f"Invalid device name {device_name}")

    async def main_task(self):
        self.log_data = [0] * _IDX_LENGTH
        self.log_data[HAL_IDX.TIME_HAL] = TPM.time()

        if SM.current_state == STATES.STARTUP:
            if not DH.data_process_exists(self.log_name):
                data_format = "L" + "B" * (_IDX_LENGTH - 1)
                DH.register_data_process(self.log_name, data_format, True, data_limit=10000)

            # restore previous device status
            if not self.restored:
                if SATELLITE.SD_CARD_AVAILABLE:
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
                                    if SATELLITE.check_device_dead(value):
                                        SATELLITE.update_device_dead(key_name.replace("_ERROR_COUNT", ""), True)
                                        self.log_info(f"Restored {key_name} to dead")
                                elif "_ERROR" in key_name:
                                    pass
                                elif "PERIPH_REBOOT_COUNT" in key_name:
                                    self.peripheral_reboot_count = value
                                    self.log_info(f"Restored {key_name} to {value}")
                                else:
                                    self.log_error(f"Unable to parse {key_name}")
                    else:
                        self.log_info("Could not restore data process, starting fresh")
                else:
                    self.log_info("No SD card available, starting fresh")
                self.restored = True

        # sample device errors from registers and boot errors
        for device_name, device_error_list in SATELLITE.SAMPLE_DEVICE_ERRORS.items():
            if device_error_list != []:
                self.log_error_handle_info(self.error_decision(device_name, device_error_list), device_name)

        # restart devices that are turned off(individual power switches)
        if self.individual_reboot_counter >= _INDIVIDUAL_REBOOT_INTERVAL:
            if self.turn_on_device != {}:
                for device_name, time in self.turn_on_device.items():
                    if self.log_data[HAL_IDX.TIME_HAL] != time:
                        SATELLITE.turn_on_device(device_name)
                        self.log_info(f"Turned on {device_name} and devices on the same power line.")
                        self.turn_on_device.pop(device_name)
            self.individual_reboot_counter = 0
        else:
            self.individual_reboot_counter += 1

        if self.graceful_reboot_counter >= _GRACEFUL_REBOOT_INTERVAL:
            if self.graceful_reboot:
                self.graceful_reboot = False
                self.peripheral_reboot_count += 1
                self.close_data_process()
                SATELLITE.graceful_reboot()
                if not DH.restore_data_process_files():
                    self.log_error("Error restoring data process files after graceful reboot")
                self.log_info("Gracefully rebooted peripheral power line.")
            self.graceful_reboot_counter = 0
        else:
            self.graceful_reboot_counter += 1

        self.log_device_status()
        DH.log_data(self.log_name, self.log_data)
        # regular reboot every 24 hours
        # TODO: delay this if the satellite is at a ground pass
        if TPM.monotonic() - SATELLITE.BOOTTIME >= _REGULAR_REBOOT_TIME:
            # TODO: graceful shutdown for payload if needed
            self.log_info("Executing regular reboot")
            self.close_data_process()
            SATELLITE.reboot()
