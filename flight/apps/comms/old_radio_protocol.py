"""
'radio_protocol.py'
======================
Python package containing protocol constants (IDs etc.).
Also contains functions for constructing/deconstructing
protocol messages.

Each message has the following header:
MESSAGE_ID : 1 byte
SEQ_COUNT  : 2 bytes
LENGTH     : 1 byte

Authors: DJ Morvay, Akshat Sahay
"""

from core.data_handler import DataHandler as DH


# Message ID definitions
class Definitions:
    SAT_HEARTBEAT_BATT = 0x00
    SAT_HEARTBEAT_SUN = 0x01
    SAT_HEARTBEAT_IMU = 0x02
    SAT_HEARTBEAT_GPS = 0x03
    SAT_HEARTBEAT_JETSON = 0x04

    GS_ACK = 0x08
    SAT_ACK = 0x09

    GS_OTA_REQ = 0x14
    SAT_OTA_RES = 0x15

    SAT_IMAGES = 0x21
    SAT_DEL_IMG1 = 0x22

    GS_STOP = 0x30

    SAT_IMG1_CMD = 0x50

    # Other constants
    REQ_ACK_NUM = 0x80


class IMAGES:
    def __init__(self):
        # Image #1 declarations
        self.image_UID = 0x0
        self.image_size = 0
        self.image_message_count = 0


def construct_message(lora_tx_message_ID):
    """
    :param lora_tx_message_ID: LoRa message ID
    :return: lora_tx_message

    Constructs TX message based on message ID
    """
    # LoRa header
    lora_tx_message = [0x00, 0x00, 0x00, 0x00]

    if lora_tx_message_ID == Definitions.SAT_HEARTBEAT_BATT:
        # Construct SAT heartbeat
        lora_tx_message = [
            Definitions.REQ_ACK_NUM | Definitions.SAT_HEARTBEAT_BATT,
            0x00,
            0x00,
            0x0A,
        ]

        # Generate LoRa payload for SAT heartbeat
        # Add system status
        lora_tx_message += [0x00, 0x00]

        # Get latest values from monitor task
        if DH.data_process_exists("monitor"):
            monitor_data = DH.get_latest_data("monitor")
        else:
            monitor_data = None

        if monitor_data is None:
            # batt_soc, currentx2, reboot, timex4
            lora_tx_message += [0x55, 0x00, 0x71, 0x00, 0x66, 0x41, 0x39, 0x80]

        else:
            # Add battery SOC
            lora_tx_message += [monitor_data["batt_soc"] & 0xFF]

            # Add current as uint16_t
            lora_tx_message += [
                (monitor_data["current"] >> 8) & 0xFF,
                monitor_data["current"] & 0xFF,
            ]

            # Add reboot count
            lora_tx_message += [0x00]

            # Add time reference as uint32_t
            time = monitor_data["time"]
            lora_tx_message += [
                (time >> 24) & 0xFF,
                (time >> 16) & 0xFF,
                (time >> 8) & 0xFF,
                time & 0xFF,
            ]

    elif lora_tx_message_ID == Definitions.SAT_HEARTBEAT_SUN:
        # Construct SAT heartbeat
        lora_tx_message = [
            Definitions.REQ_ACK_NUM | Definitions.SAT_HEARTBEAT_SUN,
            0x00,
            0x00,
            0x12,
        ]

        # Generate LoRa payload for SAT heartbeat
        # Add system status
        lora_tx_message += [0x00, 0x00]

        # Get latest values from sun vector task
        if DH.data_process_exists("sun"):
            sun_vector_data = DH.get_latest_data("sun")
        else:
            sun_vector_data = None

        if sun_vector_data is None:
            # Add sun vector
            lora_tx_message += convert_fixed_point_hp(1)
            lora_tx_message += convert_fixed_point_hp(0.9981)
            lora_tx_message += convert_fixed_point_hp(-0.9891)

            lora_tx_message += [0x66, 0x41, 0x39, 0x80]

        else:
            # Add sun vector
            lora_tx_message += convert_fixed_point_hp(sun_vector_data["x"])
            lora_tx_message += convert_fixed_point_hp(sun_vector_data["y"])
            lora_tx_message += convert_fixed_point_hp(sun_vector_data["z"])

            # Add time reference as uint32_t
            time = sun_vector_data["time"]
            lora_tx_message += [
                (time >> 24) & 0xFF,
                (time >> 16) & 0xFF,
                (time >> 8) & 0xFF,
                time & 0xFF,
            ]

    elif lora_tx_message_ID == Definitions.SAT_HEARTBEAT_IMU:
        # Construct SAT heartbeat
        lora_tx_message = [
            Definitions.REQ_ACK_NUM | Definitions.SAT_HEARTBEAT_IMU,
            0x00,
            0x00,
            0x1E,
        ]

        # Generate LoRa payload for SAT heartbeat
        # Add system status
        lora_tx_message += [0x00, 0x00]

        # Get latest values from IMU task
        if DH.data_process_exists("imu"):
            imu_data = DH.get_latest_data("imu")
        else:
            imu_data = None

        if imu_data is None:
            # Add magnetometer values
            lora_tx_message += convert_fixed_point(1)
            lora_tx_message += convert_fixed_point(2)
            lora_tx_message += convert_fixed_point(3)

            # Add gyroscope values
            lora_tx_message += convert_fixed_point(4)
            lora_tx_message += convert_fixed_point(5)
            lora_tx_message += convert_fixed_point(6)

            lora_tx_message += [0x66, 0x41, 0x39, 0x80]

        else:
            # Add magnetometer values
            lora_tx_message += convert_fixed_point(imu_data["mag_x"])
            lora_tx_message += convert_fixed_point(imu_data["mag_y"])
            lora_tx_message += convert_fixed_point(imu_data["mag_z"])

            # Add gyroscope values
            lora_tx_message += convert_fixed_point(imu_data["gyro_x"])
            lora_tx_message += convert_fixed_point(imu_data["gyro_y"])
            lora_tx_message += convert_fixed_point(imu_data["gyro_z"])

            # Add time reference as uint32_t
            time = imu_data["time"]
            lora_tx_message += [
                (time >> 24) & 0xFF,
                (time >> 16) & 0xFF,
                (time >> 8) & 0xFF,
                time & 0xFF,
            ]

    # GPS NOT IMPLEMENTED IN CURRENT VERSION!!!
    elif lora_tx_message_ID == Definitions.SAT_HEARTBEAT_GPS:
        # Construct SAT heartbeat
        lora_tx_message = [
            Definitions.REQ_ACK_NUM | Definitions.SAT_HEARTBEAT_GPS,
            0x00,
            0x00,
            0x36,
        ]

        # Generate LoRa payload for SAT heartbeat
        # Add system status
        lora_tx_message += [0x00, 0x00]

        # Add x-axis GPS ECEF position
        lora_tx_message += convert_fixed_point(2000.1)

        # Add y-axis GPS ECEF position
        lora_tx_message += convert_fixed_point(2000.2)

        # Add z-axis GPS ECEF position
        lora_tx_message += convert_fixed_point(2000.3)

        # Add x-axis GPS ECEF SD position
        lora_tx_message += convert_fixed_point(2001.1)

        # Add y-axis GPS ECEF SD position
        lora_tx_message += convert_fixed_point(2001.2)

        # Add z-axis GPS ECEF SD position
        lora_tx_message += convert_fixed_point(2001.3)

        # Add x-axis GPS ECEF velocity
        lora_tx_message += convert_fixed_point(2002.1)

        # Add y-axis GPS ECEF velocity
        lora_tx_message += convert_fixed_point(2002.2)

        # Add z-axis GPS ECEF velocity
        lora_tx_message += convert_fixed_point(2002.3)

        # Add x-axis GPS ECEF SD velocity
        lora_tx_message += convert_fixed_point(2003.1)

        # Add y-axis GPS ECEF SD velocity
        lora_tx_message += convert_fixed_point(2003.2)

        # Add z-axis GPS ECEF SD velocity
        lora_tx_message += convert_fixed_point(2003.3)

        # Add time reference as uint32_t
        lora_tx_message += [0x65, 0xF9, 0xE8, 0x4A]

    # JETSON STATUS NOT IMPLEMENTED IN CURRENT VERSION!!!
    elif lora_tx_message_ID == Definitions.SAT_HEARTBEAT_JETSON:
        # Construct SAT heartbeat
        lora_tx_message = [
            Definitions.REQ_ACK_NUM | Definitions.SAT_HEARTBEAT_JETSON,
            0x00,
            0x00,
            0x0A,
        ]

        # Generate LoRa payload for SAT heartbeat
        # Add system status
        lora_tx_message += [0x00, 0x00]

        # Add RAM usage %
        lora_tx_message += [0x2A]

        # Add disk usage %
        lora_tx_message += [0x38]

        # Add CPU temperature
        lora_tx_message += [0x4B]

        # Add GPU temperature
        lora_tx_message += [0x52]

        # Add time reference as uint32_t
        time = 1713925082
        lora_tx_message += [
            (time >> 24) & 0xFF,
            (time >> 16) & 0xFF,
            (time >> 8) & 0xFF,
            time & 0xFF,
        ]

    else:
        # Construct SAT ACK
        lora_tx_message = [
            Definitions.REQ_ACK_NUM | Definitions.SAT_ACK,
            0x00,
            0x00,
            0x36,
        ]
        lora_tx_message += [Definitions.GS_ACK, Definitions.GS_ACK, 0x00, 0x00]

    return bytes(lora_tx_message)


def deconstruct_message(lora_rx_message):
    """
    :param lora_rx_message: Received LoRa message
    :return: None

    Deconstructs RX message based on message ID
    """
    # check RX message ID
    if lora_rx_message[0] == Definitions.GS_ACK:
        print("SAT: Received GS ack!")
        sq = (lora_rx_message[1] << 8) + lora_rx_message[2]
        print("SAT: Sequence Count:", sq)
        print("SAT: Message Length:", lora_rx_message[3])

        # deconstruct message contents
        print("SAT: GS received message:", hex(lora_rx_message[4]))
        print("SAT: GS requested message:", hex(lora_rx_message[5]))
        sq = (lora_rx_message[6] << 8) + lora_rx_message[7]
        print("SAT: GS requested sequence count:", sq)


### Helper functions for converting to FP format and back ###
def convert_fixed_point(val):
    """
    :param val: Value to convert to fixed point
    :return: value in FP as byte list

    Convert value to FP with 2 int bytes, 2 dec bytes
    Range: [-32767.9999], 32767.9999]
    """
    """
    :param val: Value to convert to fixed point
    :return: value in FP as byte list

    Convert value to FP with 2 int bytes, 2 dec bytes
    Range: [-32767.9999], 32767.9999]
    """
    message_list = []
    neg_bit_flag = 0

    # If val -ve, convert to natural, set first bit of MSB
    if val < 0:
        val = -1 * val
        neg_bit_flag = 1

    # Isolate int and write to 2 bytes
    val_int = int(val)
    val_int_LSB = val_int & 0xFF
    val_int_MSB = (val_int >> 8) & 0xFF

    # Set MSB first bit as neg_bit_flag
    val_int_MSB |= neg_bit_flag << 7

    # Add the values to the test list
    message_list.append(val_int_MSB)
    message_list.append(val_int_LSB)

    # Isolate decimal and write to 2 bytes
    val_dec = val - val_int
    val_dec = int(val_dec * 65536)
    val_dec_LSB = val_dec & 0xFF
    val_dec_MSB = (val_dec >> 8) & 0xFF

    # Add the values to the test list
    message_list.append(val_dec_MSB)
    message_list.append(val_dec_LSB)

    return message_list


def convert_floating_point(message_list):
    """
    :param message_list: Byte list to convert to floating
    :return: value as floating point

    Convert FP value back to floating point
    Range: [-32767.9999], 32767.9999]
    """
    """
    :param message_list: Byte list to convert to floating
    :return: value as floating point

    Convert FP value back to floating point
    Range: [-32767.9999], 32767.9999]
    """
    val = 0
    neg_bit_flag = 0

    # Check -ve, extract LSB bytes for val, combine
    if (message_list[0] >> 7) == 1:
        message_list[0] &= 0x7F
        neg_bit_flag = 1

    # Extract bytes for val, combine
    val += (message_list[0] << 8) + message_list[1]
    val += ((message_list[2] << 8) + message_list[3]) / 65536
    if neg_bit_flag == 1:
        val = -1 * val

    return val


def convert_fixed_point_hp(val):
    """
    :param val: Value to convert to fixed point
    :return: value in FP as byte list

    Convert value to HP FP with 1 int byte, 3 dec bytes
    Range: [-128.9999999, 128.9999999]
    """
    message_list = []
    neg_bit_flag = 0

    # If val -ve, convert to natural, set first bit of MSB
    if val < 0:
        val = -1 * val
        neg_bit_flag = 1

    # Isolate int and write to 1 byte
    val_int = int(val)
    val_int_LSB = val_int & 0xFF

    # Set LSB first bit as neg_bit_flag
    val_int_LSB |= neg_bit_flag << 7

    # Add the values to the test list
    message_list.append(val_int_LSB)

    # Isolate decimal and write to 3 bytes
    val_dec = val - val_int
    val_dec = int(val_dec * 16777216)
    val_dec_LSB = val_dec & 0xFF
    val_dec_MiSB = (val_dec >> 8) & 0xFF
    val_dec_MSB = (val_dec >> 16) & 0xFF

    # Add the values to the test list
    message_list.append(val_dec_MSB)
    message_list.append(val_dec_MiSB)
    message_list.append(val_dec_LSB)

    return message_list


def convert_floating_point_hp(message_list):
    """
    :param message_list: Byte list to convert to floating
    :return: value as floating point

    Convert HP FP value back to floating point
    Range: [-127.9999999, 127.9999999]
    """
    val = 0
    neg_bit_flag = 0

    # Check -ve, extract LSB bytes for val, combine
    if (message_list[0] >> 7) == 1:
        message_list[0] &= 0x7F
        neg_bit_flag = 1

    # Extract bytes for val, combine
    val += message_list[0]
    val += ((message_list[1] << 16) + (message_list[2] << 8) + message_list[3]) / 16777216
    if neg_bit_flag == 1:
        val = -1 * val

    return val
