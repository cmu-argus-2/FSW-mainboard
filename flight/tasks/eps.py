# Electrical Power Subsystem Task

from apps.telemetry.constants import EPS_IDX
from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from hal.configuration import SATELLITE


class Task(TemplateTask):

    name = "EPS"
    ID = 0x00

    # To be removed - kept until proper logging is implemented
    data_keys = [
        "MAINBOARD_VOLTAGE",
        "MAINBOARD_CURRENT",
        "BATTERY_PACK_SOC",
        "BATTERY_PACK_REMAINING_CAPACITY_PERC",
        "BATTERY_PACK_CURRENT",
        "BATTERY_PACK_TEMPERATURE",
        "BATTERY_PACK_VOLTAGE",
        "BATTERY_PACK_MIDPOINT_VOLTAGE",
        "BATTERY_CYCLES",
        "BATTERY_PACK_TTE",
        "BATTERY_PACK_TTF",
        "BATTERY_TIME_SINCE_POWER_UP",
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
    ]

    log_data = [0.0] * 42
    batt_soc = 0
    current = 0

    async def main_task(self):

        if SM.current_state == "STARTUP":
            pass

        elif SM.current_state == "NOMINAL":

            if not DH.data_process_exists("eps"):
                DH.register_data_process("eps", self.data_keys, "ffffb", True, line_limit=50)

            # Get power system readings

            (self.batt_soc, self.current) = SATELLITE.BATTERY_POWER_MONITOR.read_voltage_current()

            self.log_data[EPS_IDX.MAINBOARD_VOLTAGE] = int(self.batt_soc * 100 / 8.4)
            self.log_data[EPS_IDX.MAINBOARD_CURRENT] = int(self.current * 10000)
            ## ADDITIONAL EPS DATA HERE ##

            ##

            print(f"[{self.ID}][{self.name}] Battery SOC: {self.batt_soc}%, Current: {self.current} mA")
