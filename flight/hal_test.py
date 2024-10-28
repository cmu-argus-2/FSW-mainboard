from hal.configuration import SATELLITE

## ---------- MAIN CODE STARTS HERE! ---------- ##

while True:
    if SATELLITE.BOARD_POWER_MONITOR is not None:
        print(SATELLITE.BOARD_POWER_MONITOR.read_voltage_current())
