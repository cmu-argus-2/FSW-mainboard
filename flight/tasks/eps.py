# Electrical Power Subsystem Task

import time

import microcontroller
from apps.eps.eps import EPS_POWER_FLAG, EPS_POWER_THRESHOLD, GET_EPS_POWER_FLAG, GET_POWER_STATUS
from apps.telemetry.constants import EPS_IDX, EPS_WARNING_IDX
from core import DataHandler as DH
from core import TemplateTask
from core import state_manager as SM
from core.states import STATES
from hal.configuration import SATELLITE


class Task(TemplateTask):
    name = "EPS"
    ID = 0x01

    # To be removed - kept until proper logging is implemented
    """data_keys = [
        "TIME",
        "EPS_POWER_FLAG",
        "MAINBOARD_TEMPERATURE",
        "MAINBOARD_VOLTAGE",
        "MAINBOARD_CURRENT",
        "BATTERY_PACK_TEMPERATURE",
        "BATTERY_PACK_REPORTED_SOC",
        "BATTERY_PACK_REPORTED_CAPACITY",
        "BATTERY_PACK_CURRENT",
        "BATTERY_PACK_VOLTAGE",
        "BATTERY_PACK_MIDPOINT_VOLTAGE",
        "BATTERY_PACK_TTE",
        "BATTERY_PACK_TTF",
        "XP_COIL_VOLTAGE",
        "XP_COIL_CURRENT",
        "XM_COIL_VOLTAGE",
        "XM_COIL_CURRENT",
        "YP_COIL_VOLTAGE",
        "YP_COIL_CURRENT",
        "YM_COIL_VOLTAGE",
        "YM_COIL_CURRENT",
        "ZP_COIL_VOLTAGE",
        "ZP_COIL_CURRENT",
        "ZM_COIL_VOLTAGE",
        "ZM_COIL_CURRENT",
        "JETSON_INPUT_VOLTAGE",
        "JETSON_INPUT_CURRENT",
        "RF_LDO_OUTPUT_VOLTAGE",
        "RF_LDO_OUTPUT_CURRENT",
        "GPS_VOLTAGE",
        "GPS_CURRENT",
        "XP_SOLAR_CHARGE_VOLTAGE",
        "XP_SOLAR_CHARGE_CURRENT",
        "XM_SOLAR_CHARGE_VOLTAGE",
        "XM_SOLAR_CHARGE_CURRENT",
        "YP_SOLAR_CHARGE_VOLTAGE",
        "YP_SOLAR_CHARGE_CURRENT",
        "YM_SOLAR_CHARGE_VOLTAGE",
        "YM_SOLAR_CHARGE_CURRENT",
        "ZP_SOLAR_CHARGE_VOLTAGE",
        "ZP_SOLAR_CHARGE_CURRENT",
        "ZM_SOLAR_CHARGE_VOLTAGE",
        "ZM_SOLAR_CHARGE_CURRENT",
    ]"""

    log_data = [0] * 43  # - use mV for voltage and mA for current (h = short integer 2 bytes)
    warning_log_data = [0] * 4
    power_buffer_dict = {
        EPS_WARNING_IDX.MAINBOARD_POWER_ALERT : [0],
        EPS_WARNING_IDX.RADIO_POWER_ALERT : [0],
        EPS_WARNING_IDX.JETSON_POWER_ALERT : [0]
        # EPS_WARNING_IDX.XP_COIL_POWER_ALERT : [0],
        # EPS_WARNING_IDX.XM_COIL_POWER_ALERT : [0],
        # EPS_WARNING_IDX.YP_COIL_POWER_ALERT : [0],
        # EPS_WARNING_IDX.YM_COIL_POWER_ALERT : [0]
    }
    log_counter = 0

    def __init__(self, id):
        super().__init__(id)
        self.name = "EPS"

    def read_vc(self, sensor):
        # read power monitor voltage and current
        board_voltage, board_current = sensor.read_voltage_current()
        return (int(board_voltage * 1000), int(board_current * 1000))

    def log_vc(self, key, voltage_idx, current_idx, voltage, current):
        # log power monitor voltage and current
        if (self.log_counter % self.frequency == 0):
            self.log_data[voltage_idx] = voltage
            self.log_data[current_idx] = current
            self.log_info(
                f"{key} Voltage: {self.log_data[voltage_idx]} mV, "
                + f"{key} Current: {self.log_data[current_idx]} mA "
            )

    def read_fuel_gauge(self):
        # read values from MAX17205
        fuel_gauge = SATELLITE.FUEL_GAUGE
        self.log_data[EPS_IDX.BATTERY_PACK_REPORTED_SOC] = int(fuel_gauge.read_soc())
        self.log_data[EPS_IDX.BATTERY_PACK_REPORTED_CAPACITY] = int(fuel_gauge.read_capacity())
        self.log_data[EPS_IDX.BATTERY_PACK_CURRENT] = int(fuel_gauge.read_current())
        self.log_data[EPS_IDX.BATTERY_PACK_VOLTAGE] = int(fuel_gauge.read_voltage())
        self.log_data[EPS_IDX.BATTERY_PACK_MIDPOINT_VOLTAGE] = int(fuel_gauge.read_midvoltage())
        self.log_data[EPS_IDX.BATTERY_PACK_TTE] = int(fuel_gauge.read_tte())
        self.log_data[EPS_IDX.BATTERY_PACK_TTF] = int(fuel_gauge.read_ttf())
        self.log_data[EPS_IDX.BATTERY_PACK_TEMPERATURE] = int(fuel_gauge.read_temperature())

    # Update MAV and set alert to indicate that resource is consuming too much power
    # TODO: add torque coil alerts?
    def set_power_alert(self, voltage, current, idx, threshold):
        power = voltage * current * 0.001  # mW
        alert, power_avg = GET_POWER_STATUS(self.power_buffer_dict[idx], power, threshold, self.frequency)
        self.warning_log_data[idx] = int(alert) & 0xFF
        if (alert):
            if (idx == EPS_WARNING_IDX.MAINBOARD_POWER_ALERT):
                self.log_warning(f"Mainboard Avg Power Consumption Warning: {power_avg} mW with threshold {threshold}")
            elif (idx == EPS_WARNING_IDX.RADIO_POWER_ALERT):
                self.log_warning(f"Radio Avg Power Consumption Warning: {power_avg} mW with threshold {threshold}")
            elif (idx == EPS_WARNING_IDX.JETSON_POWER_ALERT):
                self.log_warning(f"Jetson Avg Power Consumption Warning: {power_avg} mW with threshold {threshold}")
            # TODO: uncomment to add torque coil alerts
            # elif (idx == EPS_WARNING_IDX.XP_COIL_POWER_ALERT):
            #     self.log_warning(f"XP Coil Avg Power Consumption Warning: {power_avg} with threshold {threshold}")
            # elif (idx == EPS_WARNING_IDX.XM_COIL_POWER_ALERT):
            #    self.log_warning(f"XM Coil Avg Power Consumption Warning: {power_avg} with threshold {threshold}")
            # elif (idx == EPS_WARNING_IDX.YP_COIL_POWER_ALERT):
            #     self.log_warning(f"YP Coil Avg Power Consumption Warning: {power_avg} with threshold {threshold}")
            # elif (idx == EPS_WARNING_IDX.YM_COIL_POWER_ALERT):
            #    self.log_warning(f"YM Coil Avg Power Consumption Warning: {power_avg} with threshold {threshold}")

    async def main_task(self):
        if SM.current_state == STATES.STARTUP:
            pass

        else:
            if not DH.data_process_exists("eps"):
                data_format = (
                    "Lbhhhhb" + "L" + "h" * 3 + "L" * 2 + "h" * 30
                )  # - use mV for voltage and mA for current (h = short integer 2 bytes, L = 4 bytes)
                DH.register_data_process("eps", data_format, True, data_limit=100000)

            if not DH.data_process_exists("eps_warning"):
                data_format = (
                    "L" + "b" * 3
                )
                DH.register_data_process("eps_warning", data_format, True, data_limit=10000)

            # Get power system readings

            self.log_data[EPS_IDX.TIME_EPS] = int(time.time())
            self.warning_log_data[EPS_WARNING_IDX.TIME_EPS_WARNING] = int(time.time())

            for location, sensor in SATELLITE.POWER_MONITORS.items():
                if SATELLITE.POWER_MONITOR_AVAILABLE(location):
                    if location == "BOARD":
                        voltage, current = self.read_vc(sensor)
                        self.set_power_alert(voltage, current, EPS_WARNING_IDX.MAINBOARD_POWER_ALERT, EPS_POWER_THRESHOLD.MAINBOARD)
                        self.log_vc("Board", EPS_IDX.MAINBOARD_VOLTAGE, EPS_IDX.MAINBOARD_CURRENT, voltage, current)
                    elif location == "JETSON":
                        voltage, current = self.read_vc(sensor)
                        self.set_power_alert(voltage, current, EPS_WARNING_IDX.JETSON_POWER_ALERT, EPS_POWER_THRESHOLD.JETSON)
                        self.log_vc("Jetson", EPS_IDX.JETSON_INPUT_VOLTAGE, EPS_IDX.JETSON_INPUT_CURRENT, voltage, current)
                    elif location == "RADIO":
                        voltage, current = self.read_vc(sensor)
                        self.set_power_alert(voltage, current, EPS_WARNING_IDX.RADIO_POWER_ALERT, EPS_POWER_THRESHOLD.RADIO)
                        self.log_vc("Radio", EPS_IDX.RF_LDO_OUTPUT_VOLTAGE, EPS_IDX.RF_LDO_OUTPUT_CURRENT, voltage, current)
            # TODO: Uncomment when DRV8235 driver is in
            # for location, sensor in SATELLITE.TORQUE_DRIVERS:
            #     if SATELLITE.TORQUE_DRIVERS_AVAILABLE(location):
            #         if location == "XP":
            #           voltage, current = self.read_vc(sensor)
            #           power = voltage * current * 1000  # mW
            #           self.set_power_alert(power, EPS_WARNING_IDX.XP_COIL_POWER_ALERT, EPS_POWER_THRESHOLD.TORQUE_COIL)
            #           self.log_vc("XP Coil", EPS_IDX.XP_COIL_VOLTAGE, EPS_IDX.XP_COIL_CURRENT, voltage, current)
            #         elif location == "XM":
            #           voltage, current = self.read_vc(sensor)
            #           power = voltage * current * 1000  # mW
            #           self.set_power_alert(power, EPS_WARNING_IDX.XM_COIL_POWER_ALERT, EPS_POWER_THRESHOLD.TORQUE_COIL)
            #           self.log_vc("XM Coil", EPS_IDX.XM_COIL_VOLTAGE, EPS_IDX.XM_COIL_CURRENT, voltage, current)
            #         elif location == "YP":
            #           voltage, current = self.read_vc(sensor)
            #           power = voltage * current * 1000  # mW
            #           self.set_power_alert(power, EPS_WARNING_IDX.YP_COIL_POWER_ALERT, EPS_POWER_THRESHOLD.TORQUE_COIL)
            #           self.log_vc("YP Coil", EPS_IDX.YP_COIL_VOLTAGE, EPS_IDX.YP_COIL_CURRENT, voltage, current)
            #         elif location == "YM":
            #           voltage, current = self.read_vc(sensor)
            #           power = voltage * current * 1000  # mW
            #           self.set_power_alert(power, EPS_WARNING_IDX.YM_COIL_POWER_ALERT, EPS_POWER_THRESHOLD.TORQUE_COIL)
            #           self.log_vc("YM Coil", EPS_IDX.YM_COIL_VOLTAGE, EPS_IDX.YM_COIL_CURRENT, voltage, current)

            if self.log_counter % self.frequency == 0:
                self.log_data[EPS_IDX.MAINBOARD_TEMPERATURE] = int(microcontroller.cpu.temperature * 100)
                self.log_info(f"CPU temperature: {self.log_data[EPS_IDX.MAINBOARD_TEMPERATURE]} °cC ")

                if SATELLITE.FUEL_GAUGE_AVAILABLE:
                    self.read_fuel_gauge()
                    self.log_info(f"Battery Pack Temperature: {self.log_data[EPS_IDX.BATTERY_PACK_TEMPERATURE]}°cC")
                    self.log_info(f"Battery Pack Reported SOC: {self.log_data[EPS_IDX.BATTERY_PACK_REPORTED_SOC]}% ")
                    self.log_info(f"Battery Pack Reported Capacity: {self.log_data[EPS_IDX.BATTERY_PACK_REPORTED_CAPACITY]} mAh ")
                    self.log_info(f"Battery Pack Current: {self.log_data[EPS_IDX.BATTERY_PACK_CURRENT]} mA ")
                    self.log_info(f"Battery Pack Voltage: {self.log_data[EPS_IDX.BATTERY_PACK_VOLTAGE]} mV ")
                    self.log_info(f"Battery Pack Midpoint Voltage: {self.log_data[EPS_IDX.BATTERY_PACK_MIDPOINT_VOLTAGE]} mV ")
                    self.log_info(f"Battery Pack Time-to-Empty: {self.log_data[EPS_IDX.BATTERY_PACK_TTE]} seconds ")
                    self.log_info(f"Battery Pack Time-to-Full: {self.log_data[EPS_IDX.BATTERY_PACK_TTF]} seconds ")

                    soc = self.log_data[EPS_IDX.BATTERY_PACK_REPORTED_SOC]
                    curr_flag = self.log_data[EPS_IDX.EPS_POWER_FLAG]
                    flag = GET_EPS_POWER_FLAG(curr_flag, soc)
                    if flag != EPS_POWER_FLAG.NONE:
                        self.log_data[EPS_IDX.EPS_POWER_FLAG] = int(flag)
                        self.log_info(f"EPS state: {self.log_data[EPS_IDX.EPS_POWER_FLAG]} ")
                    else:
                        self.log_error("EPS state invalid; SOC or power flag may be corrupted")

                DH.log_data("eps", self.log_data)
            DH.log_data("eps_warning", self.warning_log_data)
            self.log_counter += 1
