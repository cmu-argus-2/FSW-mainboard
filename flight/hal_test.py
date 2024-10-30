# from hal.configuration import SATELLITE

# # ---------- MAIN CODE STARTS HERE! ---------- ##
# boot_errors = SATELLITE.boot_sequence()
# print("ARGUS-1 booted.")
# print(f"Boot Errors: {boot_errors}")

# # Board Power Monitor Test
# # while True:
# #     if SATELLITE.BOARD_POWER_MONITOR is not None:
# #         print(SATELLITE.BOARD_POWER_MONITOR.read_voltage_current())

# # charger test
# # while True:
# #     if SATELLITE.CHARGER is not None:
# #         print(SATELLITE.CHARGER.charger_status1())

# # imu test
# while True:
#     if SATELLITE.IMU is not None:
#         print(SATELLITE.IMU.gyro())


import time
import board, busio
from hal.drivers.bmx160 import BMX160

# set up BMX160 through I2C # note: also supports SPI communication through the BMX160_SPI class
i2c = busio.I2C(board.SCL1, board.SDA1) 
bmx = BMX160(i2c, 0x69)

# conservative warm-up time
time.sleep(0.1) 

while True:
    # Just call e.g. bmx.gyro to read the gyro value
    print("gyroscope:", bmx.gyro())
    print("accelerometer:", bmx.accel())
    print("magnetometer:", bmx.mag())