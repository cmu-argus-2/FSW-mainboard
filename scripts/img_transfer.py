
import time
import struct
import logging
from hal.configuration import SATELLITE
from apps.payload.uart_comms import PayloadUART as PU
from PIL import Image
from io import BytesIO


_NUM_IMG_TO_MAINTAIN_READY = 5  # Number of images to maintain in memory at least
image_array = b'' # Initialize byte array for image being received

PACKET_SIZE = 512       # num bytes
CRC5_SIZE = 1           # num bytes for crc5 (5 bits will be used)

STRUCT_FORMAT_UINT32 = '<I'  # Little-endian unsigned integer (4 bytes)
ID_START = 0
LEN_START = ID_START + 4
DATA_START = LEN_START + 4
DATA_END = DATA_START + 246

def create_crc5_packet(data_bytes):
    """Calculate CRC5 for a full 64-bit (8-byte) block."""
    num_bytes = PACKET_SIZE
    num_bits = num_bytes * 8
    polynomial = 0x05  # CRC5 polynomial (x^5 + x^2 + 1)
    crc = 0x1F  # initial CRC value

    data_int = int.from_bytes(data_bytes, 'big')  # bytes to int to do ops
    for i in range(num_bits):
        if (crc & 0x10) ^ (data_int & (1 << (num_bits-1))):
            crc = ((crc << 1) ^ polynomial) & 0x1F
        else:
            crc = (crc << 1) & 0x1F
        data_int <<= 1

    return (data_bytes << 8) | bytes([crc])  # Append 5-bit CRC to data

def verify_crc5_packet(packet):
    """Verify CRC5 for an 8-byte (64-bit) block."""
    data_bytes = packet[:-1]  # data minus crc
    # received_crc = packet[-1] >> 3  # crc is the whole byte shifted by 3
    computed_packet = create_crc5_packet(data_bytes)
    # computed_crc = computed_packet[-1] >> 3  # get only crc
    return packet == computed_packet


class ImageHandler():
    def __init__(self):
        self.images = []  # List to store images in memory

    def add_image(self, image_data):
        if len(self.images) >= _NUM_IMG_TO_MAINTAIN_READY:
            self.images.pop(0)  # Remove the oldest image if at capacity
        self.images.append(image_data)

    def save_image_to_disk(self, image_data, filename):
        with open(filename, 'wb') as f:
            f.write(image_data)


    def get_latest_image(self):
        if self.images:
            return self.images[-1]  # Return the most recent image
        return None

 
class ImageTransferHandler():
    def __init__(self):
        self.image_handler = ImageHandler()
        self.handshake_complete = False
        self.uart = PU.connect()
        self.is_connected = PU.is_connected
        self.image_array = b''

    def disconnect(self):
        PU.disconnect()
        self.is_connected = PU.is_connected

    def send(self, data):
        if self.is_connected:
            PU.send(data)
    
    def receive(self):
        if self.is_connected:
            received = PU.receive()
            if (len(received) >= PACKET_SIZE + CRC5_SIZE):
                return received #TODO see if this is an issue
        return None

    def image_array_append(self, data):
        self.image_array += data
        

    def deconstruct_received_bytes(self, received_bytes):
        # Deconstruct the received bytes from array into components: length, data,
        # The received bytes is like this -> | id (4 bytes) | length (4 bytes) | data (up to 246 bytes) | crc (1 byte) |

        packet_id = received_bytes[ID_START:LEN_START]
        data_length = received_bytes[LEN_START:DATA_START]
        data_payload_raw = received_bytes[DATA_START:DATA_END+CRC5_SIZE]
        # crc = received_bytes[DATA_END:DATA_END + CRC5_SIZE]

        return {
            'packet_id': packet_id,
            'data_length': data_length,
            'data': data_payload_raw #Also includes crc
        }

def image_receiver_task():
    # Connect to the mainboard
    handler = ImageTransferHandler()
    if not handler.is_connected:
        return 0
    
    start_time = time.time()

    # Initiate handshake and wait for ack and start image collection signal
    # If HANDSHAKE fails after 3 retries, abort mission and log failure
    timeout_shake = 0
    retry = 0
    while (not handler.handshake_complete and retry < 3):
        handler.send(b'START')
        while not handler.handshake_complete: 
            received = handler.receive() #Returns a byttearray
            if received == b'SENDING':
                handler.send(b'ACK')
                handler.handshake_complete = True
                break
            timeout_shake = time.time() - start_time
            if timeout_shake > 30: #Retry handshake 3 times Consider changing to a timeout based on actual time
                retry += 1
                timeout_shake = 0
                break
        if retry >= 5:
            handler.disconnect()
            return 0

    # Receive packets until full image is received'
    start_time = time.time()
    timeout = 0
    while True:
        received = handler.receive()
        if received is None:
            # keep waiting for timeout 
            timeout = time.time() - start_time
            if timeout > 30:  # Timeout after a certain period
                handler.disconnect()
                return 0
            continue
        timeout = 0
        packet_info = handler.deconstruct_received_bytes(received)

        data = packet_info['data']

        # While receiving packets, verify the crc5 checksum for each packet
        if not handler.verify_crc5_packet(data):
            handler.send(b'NACK')
            continue
        else:
            # Reconstruct image from packets
            handler.image_array_append(data[:-1]) # Append data without crc
            handler.send(b'ACK')

        # TODO Check for end of image signal or condition to break the loop
        if packet_info['packet_id'] == -1: # last packet id is -1
            break

    # Save the reconstructed image
    handler.image_handler.save_image_to_disk(handler.image_array, 'latest_image.jpg')
    return 1
    