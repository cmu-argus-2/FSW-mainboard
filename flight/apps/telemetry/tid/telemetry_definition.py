"""
Telemetry Format Configuration
Shared between satellite (CircuitPython) and ground station (Python)

Contains:
- Format definitions for all telemetry messages
- Helper functions for packing/unpacking data
- Fixed-point conversion functions

Custom Format Types:
- 'X': Fixed-point high-precision (4 bytes, range: -127.999 to 127.999)
- 'Y': Fixed-point low-precision (4 bytes, range: -32767.999 to 32767.999)
- Standard struct formats: B, b, H, h, I, i, L, l, Q, q, f, d
"""

# ============================================================================
# FORMAT TYPE DEFINITIONS
# ============================================================================

# Custom format identifiers
FORMAT_FIXED_POINT_HP = 'X'  # High-precision fixed point
FORMAT_FIXED_POINT_LP = 'Y'  # Low-precision fixed point

# ============================================================================
# MESSAGE IDS AND SIZES
# ============================================================================

# TM frame sizes (payload only, excluding 4-byte header)
# TM_NOMINAL_SIZE = 211
# TM_HAL_SIZE = 46
# TM_STORAGE_SIZE = 74
# TM_PAYLOAD_SIZE = 0

# Message IDs
MSG_ID_SAT_HEARTBEAT = 0x01
MSG_ID_SAT_TM_HAL = 0x02
MSG_ID_SAT_TM_STORAGE = 0x03
MSG_ID_SAT_TM_NOMINAL = 0x05



# ============================================================================
# TELEMETRY FORMAT DEFINITIONS
# ============================================================================

HEARTBEAT_NOMINAL_FORMAT = {
    "CDH": [
        ("TIME", "I"),                      # Unsigned Long (4 bytes) - Unix timestamp
        ("SC_STATE", "B"),                  # Unsigned Byte (1 byte) - Spacecraft state
        ("SD_USAGE", "I"),                  # Unsigned Long (4 bytes) - SD card usage in bytes
        ("CURRENT_RAM_USAGE", "B"),         # Unsigned Byte (1 byte) - RAM usage percentage
        ("REBOOT_COUNT", "B"),              # Unsigned Byte (1 byte) - Number of reboots
        ("WATCHDOG_TIMER", "B"),            # Unsigned Byte (1 byte) - Watchdog timer status
        ("HAL_BITFLAGS", "B"),              # Unsigned Byte (1 byte) - Hardware abstraction layer status flags
        ("DETUMBLING_ERROR_FLAG", "B")      # Unsigned Byte (1 byte) - Detumbling error flag
        
    ],
    "EPS": [
        ("EPS_POWER_FLAG", "B"),                    # Unsigned Byte (1 byte) - Low power mode flag
        ("MAINBOARD_TEMPERATURE", "h"),             # Signed Short (2 bytes) - CPU temp in 0.1°C
        ("MAINBOARD_VOLTAGE", "h"),                 # Signed Short (2 bytes) - Mainboard voltage in mV
        ("MAINBOARD_CURRENT", "h"),                 # Signed Short (2 bytes) - Mainboard current in mA
        ("BATTERY_PACK_TEMPERATURE", "h"),          # Signed Short (2 bytes) - Battery temp in 0.1°C
        ("BATTERY_PACK_REPORTED_SOC", "B"),         # Unsigned Byte (1 byte) - State of charge %
        ("BATTERY_PACK_REPORTED_CAPACITY", "H"),    # Unsigned Short (2 bytes) - Remaining capacity in mAh
        ("BATTERY_PACK_CURRENT", "h"),              # Signed Short (2 bytes) - Battery current in mA (+ charging, - discharging)
        ("BATTERY_PACK_VOLTAGE", "h"),              # Signed Short (2 bytes) - Battery voltage in mV
        ("BATTERY_PACK_MIDPOINT_VOLTAGE", "h"),     # Signed Short (2 bytes) - Battery midpoint voltage in mV
        ("BATTERY_PACK_TTE", "I"),                  # Unsigned Long (4 bytes) - Time to empty in seconds
        ("BATTERY_PACK_TTF", "I"),                  # Unsigned Long (4 bytes) - Time to full in seconds
        ("XP_COIL_VOLTAGE", "h"),                   # Signed Short (2 bytes) - X+ magnetorquer voltage in mV
        ("XP_COIL_CURRENT", "h"),                   # Signed Short (2 bytes) - X+ magnetorquer current in mA
        ("XM_COIL_VOLTAGE", "h"),                   # Signed Short (2 bytes) - X- magnetorquer voltage in mV
        ("XM_COIL_CURRENT", "h"),                   # Signed Short (2 bytes) - X- magnetorquer current in mA
        ("YP_COIL_VOLTAGE", "h"),                   # Signed Short (2 bytes) - Y+ magnetorquer voltage in mV
        ("YP_COIL_CURRENT", "h"),                   # Signed Short (2 bytes) - Y+ magnetorquer current in mA
        ("YM_COIL_VOLTAGE", "h"),                   # Signed Short (2 bytes) - Y- magnetorquer voltage in mV
        ("YM_COIL_CURRENT", "h"),                   # Signed Short (2 bytes) - Y- magnetorquer current in mA
        ("ZP_COIL_VOLTAGE", "h"),                   # Signed Short (2 bytes) - Z+ magnetorquer voltage in mV
        ("ZP_COIL_CURRENT", "h"),                   # Signed Short (2 bytes) - Z+ magnetorquer current in mA
        ("ZM_COIL_VOLTAGE", "h"),                   # Signed Short (2 bytes) - Z- magnetorquer voltage in mV
        ("ZM_COIL_CURRENT", "h"),                   # Signed Short (2 bytes) - Z- magnetorquer current in mA
        ("JETSON_INPUT_VOLTAGE", "h"),              # Signed Short (2 bytes) - Jetson payload computer input voltage in mV
        ("JETSON_INPUT_CURRENT", "h"),              # Signed Short (2 bytes) - Jetson payload computer input current in mA
        ("RF_LDO_OUTPUT_VOLTAGE", "h"),             # Signed Short (2 bytes) - RF radio LDO output voltage in mV
        ("RF_LDO_OUTPUT_CURRENT", "h"),             # Signed Short (2 bytes) - RF radio LDO output current in mA
        ("GPS_VOLTAGE", "h"),                       # Signed Short (2 bytes) - GPS receiver voltage in mV
        ("GPS_CURRENT", "h"),                       # Signed Short (2 bytes) - GPS receiver current in mA
        ("XP_SOLAR_CHARGE_VOLTAGE", "h"),           # Signed Short (2 bytes) - X+ solar panel charging voltage in mV
        ("XP_SOLAR_CHARGE_CURRENT", "h"),           # Signed Short (2 bytes) - X+ solar panel charging current in mA
        ("XM_SOLAR_CHARGE_VOLTAGE", "h"),           # Signed Short (2 bytes) - X- solar panel charging voltage in mV
        ("XM_SOLAR_CHARGE_CURRENT", "h"),           # Signed Short (2 bytes) - X- solar panel charging current in mA
        ("YP_SOLAR_CHARGE_VOLTAGE", "h"),           # Signed Short (2 bytes) - Y+ solar panel charging voltage in mV
        ("YP_SOLAR_CHARGE_CURRENT", "h"),           # Signed Short (2 bytes) - Y+ solar panel charging current in mA
        ("YM_SOLAR_CHARGE_VOLTAGE", "h"),           # Signed Short (2 bytes) - Y- solar panel charging voltage in mV
        ("YM_SOLAR_CHARGE_CURRENT", "h"),           # Signed Short (2 bytes) - Y- solar panel charging current in mA
        ("ZP_SOLAR_CHARGE_VOLTAGE", "h"),           # Signed Short (2 bytes) - Z+ solar panel charging voltage in mV
        ("ZP_SOLAR_CHARGE_CURRENT", "h"),           # Signed Short (2 bytes) - Z+ solar panel charging current in mA
        ("ZM_SOLAR_CHARGE_VOLTAGE", "h"),           # Signed Short (2 bytes) - Z- solar panel charging voltage in mV
        ("ZM_SOLAR_CHARGE_CURRENT", "h"),           # Signed Short (2 bytes) - Z- solar panel charging current in mA
    ],
    "ADCS": [
        ("MODE", "B"),                              # Unsigned Byte (1 byte) - ADCS operation mode
        ("GYRO_X", FORMAT_FIXED_POINT_HP),          # Fixed-point HP (4 bytes) - X-axis angular velocity in rad/s
        ("GYRO_Y", FORMAT_FIXED_POINT_HP),          # Fixed-point HP (4 bytes) - Y-axis angular velocity in rad/s
        ("GYRO_Z", FORMAT_FIXED_POINT_HP),          # Fixed-point HP (4 bytes) - Z-axis angular velocity in rad/s
        ("MAG_X", FORMAT_FIXED_POINT_HP),           # Fixed-point HP (4 bytes) - X-axis magnetic field in μT
        ("MAG_Y", FORMAT_FIXED_POINT_HP),           # Fixed-point HP (4 bytes) - Y-axis magnetic field in μT
        ("MAG_Z", FORMAT_FIXED_POINT_HP),           # Fixed-point HP (4 bytes) - Z-axis magnetic field in μT
        ("SUN_STATUS", "B"),                        # Unsigned Byte (1 byte) - Sun sensor validity status (0=invalid, 1=valid)
        ("SUN_VEC_X", FORMAT_FIXED_POINT_HP),       # Fixed-point HP (4 bytes) - Sun vector X component (unit vector)
        ("SUN_VEC_Y", FORMAT_FIXED_POINT_HP),       # Fixed-point HP (4 bytes) - Sun vector Y component (unit vector)
        ("SUN_VEC_Z", FORMAT_FIXED_POINT_HP),       # Fixed-point HP (4 bytes) - Sun vector Z component (unit vector)
        ("LIGHT_SENSOR_XP", "H"),                   # Unsigned Short (2 bytes) - X+ face light sensor reading (raw ADC 0-4095)
        ("LIGHT_SENSOR_XM", "H"),                   # Unsigned Short (2 bytes) - X- face light sensor reading (raw ADC 0-4095)
        ("LIGHT_SENSOR_YP", "H"),                   # Unsigned Short (2 bytes) - Y+ face light sensor reading (raw ADC 0-4095)
        ("LIGHT_SENSOR_YM", "H"),                   # Unsigned Short (2 bytes) - Y- face light sensor reading (raw ADC 0-4095)
        ("LIGHT_SENSOR_ZP1", "H"),                  # Unsigned Short (2 bytes) - Z+ face light sensor 1 reading (raw ADC 0-4095)
        ("LIGHT_SENSOR_ZP2", "H"),                  # Unsigned Short (2 bytes) - Z+ face light sensor 2 reading (raw ADC 0-4095)
        ("LIGHT_SENSOR_ZP3", "H"),                  # Unsigned Short (2 bytes) - Z+ face light sensor 3 reading (raw ADC 0-4095)
        ("LIGHT_SENSOR_ZP4", "H"),                  # Unsigned Short (2 bytes) - Z+ face light sensor 4 reading (raw ADC 0-4095)
        ("LIGHT_SENSOR_ZM", "H"),                   # Unsigned Short (2 bytes) - Z- face light sensor reading (raw ADC 0-4095)
        ("XP_COIL_STATUS", "B"),                    # Unsigned Byte (1 byte) - X+ magnetorquer status (0=off, 1=on)
        ("XM_COIL_STATUS", "B"),                    # Unsigned Byte (1 byte) - X- magnetorquer status (0=off, 1=on)
        ("YP_COIL_STATUS", "B"),                    # Unsigned Byte (1 byte) - Y+ magnetorquer status (0=off, 1=on)
        ("YM_COIL_STATUS", "B"),                    # Unsigned Byte (1 byte) - Y- magnetorquer status (0=off, 1=on)
        ("ZP_COIL_STATUS", "B"),                    # Unsigned Byte (1 byte) - Z+ magnetorquer status (0=off, 1=on)
        ("ZM_COIL_STATUS", "B"),                    # Unsigned Byte (1 byte) - Z- magnetorquer status (0=off, 1=on)
    ],
    "GPS": [
        ("MESSAGE_ID", "B"),                        # Unsigned Byte (1 byte) - GPS message type ID
        ("FIX_MODE", "B"),                          # Unsigned Byte (1 byte) - GPS fix quality (0=no fix, 2=2D fix, 3=3D fix)
        ("NUMBER_OF_SV", "B"),                      # Unsigned Byte (1 byte) - Number of satellites used in position fix
        ("GNSS_WEEK", "H"),                         # Unsigned Short (2 bytes) - GPS week number since epoch
        ("GNSS_TOW", "I"),                          # Unsigned Long (4 bytes) - GPS time of week in milliseconds
        ("LATITUDE", "i"),                          # Signed Long (4 bytes) - Latitude in 1e-7 degrees (divide by 10^7 for decimal degrees)
        ("LONGITUDE", "i"),                         # Signed Long (4 bytes) - Longitude in 1e-7 degrees (divide by 10^7 for decimal degrees)
        ("ELLIPSOID_ALT", "i"),                     # Signed Long (4 bytes) - Altitude above WGS84 ellipsoid in cm
        ("MEAN_SEA_LVL_ALT", "i"),                  # Signed Long (4 bytes) - Altitude above mean sea level in cm
        ("ECEF_X", "i"),                            # Signed Long (4 bytes) - ECEF X position coordinate in cm
        ("ECEF_Y", "i"),                            # Signed Long (4 bytes) - ECEF Y position coordinate in cm
        ("ECEF_Z", "i"),                            # Signed Long (4 bytes) - ECEF Z position coordinate in cm
        ("ECEF_VX", "i"),                           # Signed Long (4 bytes) - ECEF X velocity in cm/s
        ("ECEF_VY", "i"),                           # Signed Long (4 bytes) - ECEF Y velocity in cm/s
        ("ECEF_VZ", "i"),                           # Signed Long (4 bytes) - ECEF Z velocity in cm/s
    ],
}

TM_STORAGE_FORMAT = {
    "CDH": [
        ("TIME", "I"),                      # Unsigned Long (4 bytes) - Unix timestamp
        ("SC_STATE", "B"),                  # Unsigned Byte (1 byte) - Spacecraft state
        ("SD_USAGE", "I"),                  # Unsigned Long (4 bytes) - SD card usage in bytes
        ("CURRENT_RAM_USAGE", "B"),         # Unsigned Byte (1 byte) - RAM usage percentage
        ("REBOOT_COUNT", "B"),              # Unsigned Byte (1 byte) - Number of reboots
        ("WATCHDOG_TIMER", "B"),            # Unsigned Byte (1 byte) - Watchdog timer status
        ("HAL_BITFLAGS", "B"),              # Unsigned Byte (1 byte) - Hardware abstraction layer status flags
        ("DETUMBLING_ERROR_FLAG", "B"),     # Unsigned Byte (1 byte) - Detumbling error flag
    ],
    "STORAGE": [
        ("TOTAL", "I"),                             # Unsigned Long (4 bytes) - Total SD card usage in bytes
        ("CDH_NUM_FILES", "I"),                     # Unsigned Long (4 bytes) - Number of CDH (Command & Data Handling) files stored
        ("CDH_DIR_SIZE", "I"),                      # Unsigned Long (4 bytes) - CDH directory total size in bytes
        ("EPS_NUM_FILES", "I"),                     # Unsigned Long (4 bytes) - Number of EPS (Electrical Power System) files stored
        ("EPS_DIR_SIZE", "I"),                      # Unsigned Long (4 bytes) - EPS directory total size in bytes
        ("ADCS_NUM_FILES", "I"),                    # Unsigned Long (4 bytes) - Number of ADCS (Attitude Determination & Control) files stored
        ("ADCS_DIR_SIZE", "I"),                     # Unsigned Long (4 bytes) - ADCS directory total size in bytes
        ("COMMS_NUM_FILES", "I"),                   # Unsigned Long (4 bytes) - Number of communications files stored
        ("COMMS_DIR_SIZE", "I"),                    # Unsigned Long (4 bytes) - Communications directory total size in bytes
        ("GPS_NUM_FILES", "I"),                     # Unsigned Long (4 bytes) - Number of GPS files stored
        ("GPS_DIR_SIZE", "I"),                      # Unsigned Long (4 bytes) - GPS directory total size in bytes
        ("PAYLOAD_NUM_FILES", "I"),                 # Unsigned Long (4 bytes) - Number of payload files stored
        ("PAYLOAD_DIR_SIZE", "I"),                  # Unsigned Long (4 bytes) - Payload directory total size in bytes
        ("COMMAND_NUM_FILES", "I"),                 # Unsigned Long (4 bytes) - Number of command log files stored
        ("COMMAND_DIR_SIZE", "I"),                  # Unsigned Long (4 bytes) - Command logs directory total size in bytes
    ],
}

TM_HAL_FORMAT = {
    "CDH": [
        ("TIME", "I"),                      # Unsigned Long (4 bytes) - Unix timestamp
        ("SC_STATE", "B"),                  # Unsigned Byte (1 byte) - Spacecraft state
        ("SD_USAGE", "I"),                  # Unsigned Long (4 bytes) - SD card usage in bytes
        ("CURRENT_RAM_USAGE", "B"),         # Unsigned Byte (1 byte) - RAM usage percentage
        ("REBOOT_COUNT", "B"),              # Unsigned Byte (1 byte) - Number of reboots
        ("WATCHDOG_TIMER", "B"),            # Unsigned Byte (1 byte) - Watchdog timer status
        ("HAL_BITFLAGS", "B"),              # Unsigned Byte (1 byte) - Hardware abstraction layer status flags
        ("DETUMBLING_ERROR_FLAG", "B"),     # Unsigned Byte (1 byte) - Detumbling error flag
    ],
    # TODO: Add HAL-specific fields (error codes, hardware status details, etc.)
}