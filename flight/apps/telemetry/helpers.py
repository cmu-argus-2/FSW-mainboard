"""
Helper functions for converting to fixed point format and back.

Authors: Akshat Sahay, Ibrahima Sory Sow, DJ Morvay
"""


def convert_float_to_fixed_point_lp(val):
    """
    Convert float value to fixed point with 2 integer bytes, 2 decimal bytes (low-precision).
    Range: [-32767.9999, 32767.9999]
    :param val: Value to convert to fixed point
    :return: value in fixed point as a list of bytes
    """
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
    return [val_int_MSB, val_int_LSB, val_dec_MSB, val_dec_LSB]


def convert_fixed_point_to_float_lp(message_list):
    """
    Convert low-precision fixed point value back to floating point.
    Range: [-32767.9999, 32767.9999]
    :param message_list: Byte list to convert to floating
    :return: value as floating point
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
    :param val: Value to convert to fixed point
    :return: value in FP as byte list
    Convert float value to fixed point with 1 integer bytes, 3 decimal bytes (high-precision).
    Range: [-127.9999999, 127.9999999]
    """
    # Handle negative flag and convert to positive if necessary
    neg_bit_flag = 1 if val < 0 else 0
    val = abs(val)

    # Separate integer and decimal parts
    val_int = int(val)
    val_dec = int((val - val_int) * 16777216)

    # Combine neg_bit_flag with integer part
    val_int_byte = (val_int & 0x7F) | (neg_bit_flag << 7)

    # Pack into message list
    message_list = [val_int_byte, (val_dec >> 16) & 0xFF, (val_dec >> 8) & 0xFF, val_dec & 0xFF]

    return message_list


def convert_fixed_point_to_float_hp(message_list):
    """
    :param message_list: Byte list to convert to floating
    :return: value as floating point

    Convert high-precision fixed point value back to floating point
    Range: [-128.9999999, 128.9999999]
    """
    # Extract integer part and negative flag
    val_int = message_list[0] & 0x7F
    neg_bit_flag = message_list[0] >> 7

    # Combine the decimal bytes
    val_dec = (message_list[1] << 16) | (message_list[2] << 8) | message_list[3]
    val = val_int + val_dec / 16777216  # 2^24

    # Apply the negative flag if necessary
    if neg_bit_flag:
        val = -val

    return val
