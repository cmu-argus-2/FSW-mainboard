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
# HELPER FUNCTIONS - FIXED POINT CONVERSION
# ============================================================================

def convert_float_to_fixed_point_lp(val):
    """
    Convert float value to fixed point with 2 integer bytes, 2 decimal bytes (low-precision).
    Range: [-32767.9999, 32767.9999]
    
    Args:
        val: Float value to convert to fixed point
    
    Returns:
        bytearray: 4-byte fixed-point representation
    """
    # Check for None and NaN
    if val is None or val != val:
        return bytearray([0x00, 0x00, 0x00, 0x00])

    # Fixed-point LP range is -32768 to 32767
    if int(val) > 32767 or int(val) < -32768:
        print(f"Warning: Fixed point LP data outside of range: {val}")

    # Handle sign and absolute value
    neg_bit_flag = 1 if val < 0 else 0
    val = abs(val)

    # Isolate integer part
    val_int = int(val)
    val_int_MSB = (val_int >> 8) & 0x7F  # Only 7 bits for the value
    val_int_LSB = val_int & 0xFF

    # Set MSB first bit as neg_bit_flag
    val_int_MSB |= neg_bit_flag << 7

    # Isolate decimal part
    val_dec = int((val - val_int) * 65536)
    val_dec_MSB = (val_dec >> 8) & 0xFF
    val_dec_LSB = val_dec & 0xFF

    # Combine into a single list
    return bytearray([val_int_MSB, val_int_LSB, val_dec_MSB, val_dec_LSB])


def convert_fixed_point_to_float_lp(message_list):
    """
    Convert low-precision fixed point value back to floating point.
    Range: [-32767.9999, 32767.9999]
    
    Args:
        message_list: 4-byte bytearray to convert to float
    
    Returns:
        float: Converted value
    """
    # Check sign bit and extract integer part
    neg_bit_flag = (message_list[0] >> 7) & 1
    int_part = ((message_list[0] & 0x7F) << 8) | message_list[1]

    # Extract decimal part
    dec_part = ((message_list[2] << 8) | message_list[3]) / 65536.0

    # Combine integer and decimal parts
    val = int_part + dec_part

    # Apply the sign
    return -val if neg_bit_flag else val


def convert_float_to_fixed_point_hp(val):
    """
    Convert float value to fixed point with 1 integer byte, 3 decimal bytes (high-precision).
    Range: [-127.9999999, 127.9999999]
    
    Args:
        val: Float value to convert to fixed point
    
    Returns:
        bytearray: 4-byte fixed-point representation
    """
    # Check for None and NaN
    if val is None or val != val:
        return bytearray([0x00, 0x00, 0x00, 0x00])

    # Fixed-point HP range is -128 to 127
    if int(val) > 127 or int(val) < -128:
        print(f"Warning: Fixed point HP data outside of range: {val}")

    # Handle negative flag and convert to positive if necessary
    neg_bit_flag = 1 if val < 0 else 0
    val = abs(val)

    # Separate integer and decimal parts
    val_int = int(val)
    val_dec = int((val - val_int) * 16777216)  # 2^24

    # Combine neg_bit_flag with integer part
    val_int_byte = (val_int & 0x7F) | (neg_bit_flag << 7)

    # Pack into message list
    message_list = bytearray([
        val_int_byte,
        (val_dec >> 16) & 0xFF,
        (val_dec >> 8) & 0xFF,
        val_dec & 0xFF
    ])

    return message_list


def convert_fixed_point_to_float_hp(message_list):
    """
    Convert high-precision fixed point value back to floating point.
    Range: [-127.9999999, 127.9999999]
    
    Args:
        message_list: 4-byte bytearray to convert to float
    
    Returns:
        float: Converted value
    """
    # Extract integer part and negative flag
    val_int = message_list[0] & 0x7F
    neg_bit_flag = message_list[0] >> 7

    # Combine the decimal bytes
    val_dec = (message_list[1] << 16) | (message_list[2] << 8) | message_list[3]
    val = val_int + val_dec / 16777216.0  # 2^24

    # Apply the negative flag if necessary
    if neg_bit_flag:
        val = -val

    return val


# ============================================================================
# HELPER FUNCTIONS - INTEGER PACKING/UNPACKING
# ============================================================================

def pack_unsigned_long_int(data, idx):
    """
    Pack a 4-byte unsigned integer from data array.
    Range: [0, 4294967295]
    
    Args:
        data: List of integers
        idx: Index of the integer in the data list to pack
    
    Returns:
        bytearray: 4 bytes representing the packed integer
    """
    # Check for None and NaN
    if data[idx] is None or data[idx] != data[idx]:
        return bytearray([0x00, 0x00, 0x00, 0x00])

    # Unsigned int range is 0 to 4294967295
    if data[idx] < 0:
        print(f"Error: Unsigned int data is negative: {data[idx]}")
        return bytearray([0x00, 0x00, 0x00, 0x00])

    if data[idx] > 4294967295:
        print(f"Warning: Unsigned int data outside of range: {data[idx]}")

    return bytearray([
        (data[idx] >> 24) & 0xFF,
        (data[idx] >> 16) & 0xFF,
        (data[idx] >> 8) & 0xFF,
        data[idx] & 0xFF
    ])


def pack_signed_long_int(data, idx):
    """
    Pack a signed 4-byte integer from data array.
    Range: [-2147483648, 2147483647]
    
    Args:
        data: List of signed integers
        idx: Index of the integer in the data list to pack
    
    Returns:
        bytearray: 4 bytes representing the packed signed integer
    """
    # Check for None and NaN
    if data[idx] is None or data[idx] != data[idx]:
        return bytearray([0x00, 0x00, 0x00, 0x00])

    # Signed int range is -2147483648 to 2147483647
    if data[idx] > 2147483647 or data[idx] < -2147483648:
        print(f"Warning: Signed int data outside of range: {data[idx]}")

    # Handle signed integers by converting to unsigned before packing
    val = data[idx] & 0xFFFFFFFF
    return bytearray([
        (val >> 24) & 0xFF,
        (val >> 16) & 0xFF,
        (val >> 8) & 0xFF,
        val & 0xFF
    ])


def unpack_signed_long_int(byte_list):
    """
    Unpack a signed 4-byte integer from bytes.
    
    Args:
        byte_list: 4-byte bytearray
    
    Returns:
        int: Unpacked signed integer
    """
    # Combine the bytes into a 32-bit signed integer
    val = (byte_list[0] << 24) | (byte_list[1] << 16) | (byte_list[2] << 8) | byte_list[3]

    # Convert to signed integer if the sign bit (MSB) is set
    return val if val < 0x80000000 else val - 0x100000000


def unpack_unsigned_long_int(byte_list):
    """
    Unpack an unsigned 4-byte integer from bytes.
    
    Args:
        byte_list: 4-byte bytearray
    
    Returns:
        int: Unpacked unsigned integer
    """
    return (byte_list[0] << 24) | (byte_list[1] << 16) | (byte_list[2] << 8) | byte_list[3]


def pack_unsigned_short_int(data, idx):
    """
    Pack a 2-byte unsigned integer from data array.
    Range: [0, 65535]
    
    Args:
        data: List of integers
        idx: Index of the integer in the data list to pack
    
    Returns:
        bytearray: 2 bytes representing the packed unsigned integer
    """
    # Check for None and NaN
    if data[idx] is None or data[idx] != data[idx]:
        return bytearray([0x00, 0x00])

    if data[idx] < 0:
        print(f"Error: Unsigned short int data is negative: {data[idx]}")
        return bytearray([0x00, 0x00])

    if data[idx] > 65535:
        print(f"Warning: Unsigned short int data outside of range: {data[idx]}")

    return bytearray([
        (data[idx] >> 8) & 0xFF,
        data[idx] & 0xFF
    ])


def unpack_unsigned_short_int(byte_list):
    """
    Unpack a 2-byte unsigned integer from bytes.
    
    Args:
        byte_list: 2-byte bytearray
    
    Returns:
        int: Unpacked unsigned integer
    """
    return (byte_list[0] << 8) | byte_list[1]


def pack_signed_short_int(data, idx):
    """
    Pack a signed 2-byte integer from data array.
    Range: [-32768, 32767]
    
    Args:
        data: List of signed integers
        idx: Index of the integer in the data list to pack
    
    Returns:
        bytearray: 2 bytes representing the packed signed integer
    """
    # Check for None and NaN
    if data[idx] is None or data[idx] != data[idx]:
        return bytearray([0x00, 0x00])

    if data[idx] > 32767 or data[idx] < -32768:
        print(f"Warning: Signed short int data outside of range: {data[idx]}")

    val = data[idx] & 0xFFFF
    return bytearray([
        (val >> 8) & 0xFF,
        val & 0xFF
    ])


def unpack_signed_short_int(byte_list):
    """
    Unpack a signed 2-byte integer from bytes.
    
    Args:
        byte_list: 2-byte bytearray
    
    Returns:
        int: Unpacked signed integer
    """
    val = (byte_list[0] << 8) | byte_list[1]
    return val if val < 0x8000 else val - 0x10000


# ============================================================================
# HELPER FUNCTIONS - FORMAT SIZE CALCULATION
# ============================================================================

def get_format_size(fmt):
    """
    Get byte size for format type including custom types.
    
    Args:
        fmt: Format character ('B', 'h', 'I', 'X', 'Y', etc.)
    
    Returns:
        int: Number of bytes for this format
    """
    if fmt == FORMAT_FIXED_POINT_HP or fmt == FORMAT_FIXED_POINT_LP:
        return 4
    
    # Standard struct format sizes
    sizes = {
        'b': 1, 'B': 1,      # byte
        'h': 2, 'H': 2,      # short
        'i': 4, 'I': 4,      # int
        'l': 4, 'L': 4,      # long
        'q': 8, 'Q': 8,      # long long
        'f': 4, 'd': 8       # float, double
    }
    return sizes.get(fmt, 0)


def get_subsystem_size(fields):
    """
    Calculate total byte size for a subsystem's fields.
    
    Args:
        fields: List of (field_name, format) tuples
    
    Returns:
        int: Total size in bytes
    """
    return sum(get_format_size(fmt) for _, fmt in fields)


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