
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