# Electrical Power Subsystem Task

import time

import microcontroller
from apps.eps.eps import EPS_POWER_FLAG, GET_EPS_POWER_FLAG
from apps.telemetry.constants import EPS_IDX
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
        "CPU_TEMPERATURE",
        "BATTERY_PACK_TEMPERATURE",
        "MAINBOARD_VOLTAGE",
        "MAINBOARD_CURRENT",
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

    def __init__(self, id):
        super().__init__(id)
        self.name = "EPS"

    def read_vc(self, sensor, voltage_idx, current_idx):
        # log power monitor voltage and current
        if sensor is not None:
            board_voltage, board_current = sensor.read_voltage_current()
            self.log_data[voltage_idx] = int(board_voltage * 1000)  # mV - max 8.4V
            self.log_data[current_idx] = int(board_current * 1000)  # mA

    def read_fuel_gauge(self):
        # read values from MAX17205
        fuel_gauge = SATELLITE.FUEL_GAUGE
        if fuel_gauge is not None:
            self.log_data[EPS_IDX.BATTERY_PACK_REPORTED_SOC] = int(fuel_gauge.read_soc())
            self.log_data[EPS_IDX.BATTERY_PACK_REPORTED_CAPACITY] = int(fuel_gauge.read_capacity())
            self.log_data[EPS_IDX.BATTERY_PACK_CURRENT] = int(fuel_gauge.read_current())
            self.log_data[EPS_IDX.BATTERY_PACK_VOLTAGE] = int(fuel_gauge.read_voltage())
            self.log_data[EPS_IDX.BATTERY_PACK_MIDPOINT_VOLTAGE] = int(fuel_gauge.read_midvoltage())
            self.log_data[EPS_IDX.BATTERY_PACK_TTE] = int(fuel_gauge.read_tte())
            self.log_data[EPS_IDX.BATTERY_PACK_TTF] = int(fuel_gauge.read_ttf())
            self.log_data[EPS_IDX.BATTERY_PACK_TEMPERATURE] = int(fuel_gauge.read_temperature())
            return True
        else:
            return False

    async def main_task(self):
        if SM.current_state == STATES.STARTUP:
            pass

        else:
            if not DH.data_process_exists("eps"):
                data_format = (
                    "Lbhhhhb" + "h" * 4 + "L" * 2 + "h" * 30
                )  # - use mV for voltage and mA for current (h = short integer 2 bytes, L = 4 bytes)
                DH.register_data_process("eps", data_format, True, data_limit=100000)

            # Get power system readings

            self.log_data[EPS_IDX.TIME_EPS] = int(time.time())

            for key in SATELLITE.POWER_MONITORS:
                if key == "BOARD":
                    self.read_vc(SATELLITE.POWER_MONITORS[key], EPS_IDX.MAINBOARD_VOLTAGE, EPS_IDX.MAINBOARD_CURRENT)
                    self.log_info(
                        f"Board Voltage: {self.log_data[EPS_IDX.MAINBOARD_VOLTAGE]} mV, "
                        + f"Board Current: {self.log_data[EPS_IDX.MAINBOARD_CURRENT]} mA "
                    )
                elif key == "JETSON":
                    self.read_vc(SATELLITE.POWER_MONITORS[key], EPS_IDX.JETSON_INPUT_VOLTAGE, EPS_IDX.JETSON_INPUT_CURRENT)
                    self.log_info(
                        f"Jetson Voltage: {self.log_data[EPS_IDX.JETSON_INPUT_VOLTAGE]} mV, "
                        + f"Jetson Current: {self.log_data[EPS_IDX.JETSON_INPUT_CURRENT]} mA"
                    )
                elif key == "RADIO":
                    self.read_vc(SATELLITE.POWER_MONITORS[key], EPS_IDX.RF_LDO_OUTPUT_VOLTAGE, EPS_IDX.RF_LDO_OUTPUT_CURRENT)
                    self.log_info(
                        f"Radio Voltage: {self.log_data[EPS_IDX.RF_LDO_OUTPUT_VOLTAGE]} mV, "
                        + f"Radio Current: {self.log_data[EPS_IDX.RF_LDO_OUTPUT_CURRENT]} mA"
                    )

            self.log_data[EPS_IDX.CPU_TEMPERATURE] = int(microcontroller.cpu.temperature * 100)
            self.log_info(f"CPU temperature: {self.log_data[EPS_IDX.CPU_TEMPERATURE]} °cC ")

            if self.read_fuel_gauge():
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
