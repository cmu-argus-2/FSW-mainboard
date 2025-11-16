# Payload Control Task

from apps.payload.controller import PayloadController as PC
from apps.payload.controller import PayloadState, map_state
from apps.payload.definitions import ExternalRequest
from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STATES

import time
import struct
from hal.configuration import SATELLITE
from apps.payload.uart_comms import PayloadUART as PU
from io import BytesIO

_NUM_IMG_TO_MAINTAIN_READY = 5  # Number of images to maintain in memory at least
image_array = b'' # Initialize byte array for image being received

PACKET_SIZE = 250       # num bytes TODO : MATCH WITH PAYLOAD UART
CRC5_SIZE = 1           # num bytes for crc5 (5 bits will be used)

STRUCT_FORMAT_UINT32 = '<I'  # Little-endian unsigned integer (4 bytes)
ID_START = 0
LEN_START = ID_START + 4
DATA_START = LEN_START + 4
DATA_END = DATA_START + 246

CMD_HANDSHAKE_REQUEST = 0x01
CMD_DATA_CHUNK = 0x02
CMD_ACK_READY = 0x10
CMD_ACK_OK = 0x11
CMD_NACK_CORRUPT = 0x20
CMD_NACK_LOST = 0x21
CMD_IMAGE_REQUEST = 0x06
CMD_IMAGE_RECEIVED = 0x07

class Task(TemplateTask):

    current_request = ExternalRequest.NO_ACTION

    def __init__(self, id):
        super().__init__(id)
        self.name = "PAYLOAD"

    def init_all_data_processes(self):
        # Image process
        if not DH.data_process_exists("img"):
            DH.register_image_process()  # WARNING: Image process from DH is different from regular data processes!

        # Telemetry process
        if not DH.data_process_exists("payload_tm"):
            DH.register_data_process(
                tag_name="payload_tm",
                data_format=PC.tm_process_data_format,
                persistent=True,
                data_limit=100000,
                circular_buffer_size=200,
            )

        # OD process (should be a separate file process)
        if not DH.data_process_exists("payload_od"):
            pass

        # Data process for runtime external requests from the CDH
        if not DH.data_process_exists("payload_requests"):
            DH.register_data_process(tag_name="payload_requests", data_format="B", persistent=False)

    async def main_task(self):
        if SM.current_state == STATES.STARTUP:
            return

        # Check if any external requests were received irrespective of state
        if DH.data_process_exists("payload_requests") and DH.data_available("payload_requests"):
            candidate_request = DH.get_latest_data("payload_requests")[0]
            if candidate_request != ExternalRequest.NO_ACTION:  # TODO: add timeout in-between requests
                PC.add_request(candidate_request)

        if SM.current_state != STATES.EXPERIMENT:

            if not PC.interface_injected():
                PC.load_communication_interface()

            # Need to handle issues with power control eventually or log error codes for the HAL

            self.init_all_data_processes()

            """
            Two cases:
             - Satellite has booted up and we need to initialize the payload
             - State transitioned out of EXPERIMENT and we need to stop the payload gracefully
               (forcefully in worst-case scenarios)
            """

            # TODO: This is going to change
            if PC.state != PayloadState.OFF:  # All good

                PC.add_request(ExternalRequest.TURN_OFF)

                if PC.state == PayloadState.SHUTTING_DOWN:
                    # TODO: check timeout just in case. However, this will be handled internally.
                    PC.add_request(ExternalRequest.FORCE_POWER_OFF)
                    pass

        else:  # EXPERIMENT state

            if PC.state == PayloadState.OFF:
                PC.add_request(ExternalRequest.TURN_ON)

            elif PC.state == PayloadState.READY:
                if DH.data_process_exists("img"):
                    # Check how many images we have collected in memory
                    if (
                        DH.how_many_complete_images() < _NUM_IMG_TO_MAINTAIN_READY and not PC.file_transfer_in_progress()
                    ):  # Handle this properly..
                        # TODO: add DH check on the size to clean-up not complete images (that can arise in bootup)
                        self.log_info("Not enough images in memory, requesting new image")
                        PC.add_request(ExternalRequest.REQUEST_IMAGE)
        image_receiver_task()   

        # DO NOT EXPOSE THE LOGIC IN THE TASK and KEEP EVERYTHING INTERNAL
        PC.run_control_logic()
        self.log_info(f"Payload state: {map_state(PC.state)}")


# def create_crc5_packet(data_bytes):
#     """Calculate CRC5 for a full 64-bit (8-byte) block."""
#     num_bytes = PACKET_SIZE
#     num_bits = num_bytes * 8
#     polynomial = 0x05  # CRC5 polynomial (x^5 + x^2 + 1)
#     crc = 0x1F  # initial CRC value

#     # Convert the bytearray to an integer for bitwise operations
#     data_int = int.from_bytes(data_bytes, 'big')  # bytes to int to do ops

#     for i in range(num_bits):
#         if (crc & 0x10) ^ (data_int & (1 << (num_bits-1))):
#             crc = ((crc << 1) ^ polynomial) & 0x1F
#         else:
#             crc = (crc << 1) & 0x1F
#         data_int <<= 1

#     # Now that we've computed the CRC, append it to the original data
#     # Convert the integer back to bytes, add the CRC
#     result_int = (data_int >> num_bits) | (crc << (num_bits))  # Append CRC to the data
#     result_bytes = result_int.to_bytes(num_bytes + 1, 'big')  # Convert to bytearray with CRC appended

#     return result_bytes

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

    return (data_bytes ) + bytes([crc])  # Append 5-bit CRC to data

def verify_crc5_packet(packet):
    """Verify CRC5 for an 8-byte (64-bit) block."""
    data_bytes = packet[:-1]  # data minus crc
    # received_crc = packet[-1] >> 3  # crc is the whole byte shifted by 3
    computed_packet = create_crc5_packet(data_bytes)
    print("Computed packet: ", computed_packet)
    print("Received packet: ", packet)
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
        self.image_array = {}

    def disconnect(self):
        PU.disconnect()
        self.is_connected = PU.is_connected

    def send(self, data):
        if self.is_connected:
            PU.send(data)
    
    def receive(self):
        if self.is_connected:
            received = PU.receive()
            return received # TODO TODAY
            if (len(received) >= PACKET_SIZE + CRC5_SIZE):
                return received #TODO see if this is an issue
        return None

    def image_array_append(self, data, chunk_id):
        self.image_array[chunk_id] = data

    def sort_image_array(self):
        sorted_image = bytearray()
        for key in sorted(self.image_array.keys()):
            sorted_image += self.image_array[key]
        return sorted_image

# def deconstruct_received_bytes(received_bytes):
#     # Deconstruct the received bytes from array into components: length, data,
#     # The received bytes is like this -> | id (4 bytes) | length (4 bytes) | data (up to 246 bytes) | crc (1 byte) |
#     # The received data has a padding of zeros if data is less than PACKET_SIZE
#     packet_id = received_bytes[ID_START:LEN_START]
#     data_length = received_bytes[LEN_START:DATA_START]
#     data_payload_raw = received_bytes[DATA_START:DATA_END+CRC5_SIZE]
#     # crc = received_bytes[DATA_END:DATA_END + CRC5_SIZE]

#     return {
#         'packet_id': packet_id,
#         'data_length': data_length,
#         'data': data_payload_raw #Also includes crc
#     }

# REQ:  PACKET_TYPE|REQUESTED_PACKET|INFO
# IMAGE: PACKET_TYPE|CHUNK_ID|PACKET|CRC
# ACK:  ACK_OK|CHUNK_ID or ACK_OK|PACKET_ID
# NACK:  NACK | FAILED packet ID 
# PACKET_TYPE: uint8_t
# CHUNK_ID: uint32_t
# PACKET: Byte array
# CRC: uint8_t 


# IT CAN ONLY REQUEST IMAGE PACKET FOR NOW
def create_packet(packet_id, requested_packet=None, data=None, chunk_id=None, data_length=None, last_packet=0):
    if data is not None: 
        if (type(data) is str):
            data = data.encode('utf-8')
            data_length = len(data)

    result = bytearray(PACKET_SIZE)
    if packet_id == CMD_HANDSHAKE_REQUEST: 
        # Only handle image request handshake for now
        if requested_packet == CMD_IMAGE_REQUEST:
            # info = data if data is not None else b''
            result = packet_id.to_bytes(1, byteorder='big') + requested_packet.to_bytes(1, byteorder='big') #+ info.ljust(PACKET_SIZE - 4, b'\0')
            # result = result.ljust(PACKET_SIZE, b'\0')
    
    elif packet_id == CMD_DATA_CHUNK:   
        # Data chunk packet
        result = packet_id.to_bytes(1, byteorder='big') + chunk_id.to_bytes(4, byteorder='big') + data_length.to_bytes(4, byteorder='big') + data + last_packet.to_bytes(1, byteorder='big')
        result = create_crc5_packet(result)
        # result = crc_packet.ljust(PACKET_SIZE + CRC5_SIZE, b'\0')
    
    elif packet_id == CMD_ACK_OK:
        # ACK packet
        result = packet_id.to_bytes(1, byteorder='big') + chunk_id.to_bytes(4, byteorder='big')
        # result = result.ljust(PACKET_SIZE, b'\0')
    
    elif packet_id == CMD_NACK_CORRUPT:
        # NACK packet
        result = packet_id.to_bytes(1, byteorder='big') + chunk_id.to_bytes(4, byteorder='big')
        # result = result.ljust(PACKET_SIZE, b'\0')
    
    elif packet_id == CMD_ACK_READY:
        # ACK READY packet
        result = packet_id.to_bytes(1, byteorder='big') + requested_packet.to_bytes(1, byteorder='big')
        # result = result.ljust(PACKET_SIZE, b'\0')
    elif packet_id == CMD_IMAGE_RECEIVED:
        result = packet_id.to_bytes(1, byteorder='big')
        # result = result.ljust(PACKET_SIZE, b'\0')
    return result

# Return dictionary with packet_id, chunk_id, data_length, data, crc
def read_packet(received_bytes):
    # received_bytes = received_byts.deco
    packet_id = int.from_bytes(received_bytes[0:1], byteorder='big')
    if packet_id == CMD_HANDSHAKE_REQUEST:
        requested_packet = int.from_bytes(received_bytes[1:2], byteorder='big')
        # info = received_bytes[2:].decode('utf-8').strip('\0')
        return {'packet_id': packet_id, 'requested_packet': requested_packet} #, 'data': info}
    
    elif packet_id == CMD_DATA_CHUNK:
        print("Reading data chunk packet: ", received_bytes)
        chunk_id = int.from_bytes(received_bytes[1:5], byteorder='big')
        data_length = int.from_bytes(received_bytes[5:9], byteorder='big')
        data = received_bytes[9:9+data_length]
        last_packet = received_bytes[9+data_length]
        crc = received_bytes[9+data_length+1]
        verify_crc = verify_crc5_packet(received_bytes[0:9+data_length+2])
        return {'packet_id': packet_id, 'chunk_id': chunk_id, 'data_length': data_length, 'data': data, 'last_packet': last_packet, 'crc': crc, 'crc_valid': verify_crc}
    
    elif packet_id == CMD_ACK_READY:
        ready_packet_id = int.from_bytes(received_bytes[1:2], byteorder='big')
        return {'packet_id': packet_id, 'ready_packet_id': ready_packet_id}
    
    elif packet_id == CMD_ACK_OK:
        acked_packet_id = int.from_bytes(received_bytes[1:5], byteorder='big')
        return {'packet_id': packet_id, 'acked_packet_id': acked_packet_id}
    
    elif packet_id == CMD_NACK_CORRUPT:
        failed_packet_id = int.from_bytes(received_bytes[1:5], byteorder='big')
        return {'packet_id': packet_id, 'failed_packet_id': failed_packet_id}
    
    else: # Unknown packet type
        return {'packet_id': packet_id}



# '''
def image_receiver_task():
    handler = ImageTransferHandler()
    if not handler.is_connected:
        return 0

    start_time = time.time()

    timeout_shake = 0
    retry = 0
    while (not handler.handshake_complete and retry < 3):
        start_packet = create_packet(CMD_HANDSHAKE_REQUEST, requested_packet=CMD_IMAGE_REQUEST, data=b'')
        print("Sending handshake request to payload", start_packet)
        handler.send(start_packet)

        # if not handler.handshake_complete: 
        received = handler.receive() #Returns a bytearray
        if received is None:
            continue
        old_received = received
        # print ("Handshake received raw: ", received)
        received = read_packet(received)
        # print(f"Handshake received: {received}")
        # print("Received handshake preeiosdfhn;sdffghis: *******************************", received['packet_id'], received, old_received)

        if received['packet_id'] == CMD_ACK_READY:
            # print("Handshake complete, starting image transfer")
            ack_ready_packet = create_packet(CMD_ACK_READY, requested_packet=CMD_IMAGE_REQUEST)
            handler.send(ack_ready_packet)
            handler.handshake_complete = True
            break
        # print("Received handshake is: *******************************", received['packet_id'], received, old_received)
        timeout_shake = time.time() - start_time
        if timeout_shake > 5: #Retry handshake 3 times Consider changing to a timeout based on actual time
            retry += 1
            timeout_shake = 0
            break
        if retry >= 3:
            handler.disconnect()
            return 0

    # Receive packets until full image is received'
    start_time = time.time()
    timeout = 0
    print("Starting image transfer...GROOT")
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
        # packet_info = handler.deconstruct_received_bytes(received)
        packet_info = read_packet(received)
        if packet_info['packet_id'] != CMD_DATA_CHUNK:
            continue
        if packet_info['crc_valid'] == False:
            nack_packet = create_packet(CMD_NACK_CORRUPT, chunk_id=packet_info['chunk_id'])
            handler.send(nack_packet)
            continue
        
        data_received = packet_info['data']

            # Reconstruct image from packets
        handler.image_array_append(data_received[:-1], packet_info['chunk_id']) # Append data without crc
        ack_packet = create_packet(CMD_ACK_OK, chunk_id=packet_info['chunk_id'])
        handler.send(ack_packet)

        # TODO Check for end of image signal or condition to break the loop
        if packet_info['last_packet'] == 1: # last packet id is 0
            break

    # Save the reconstructed image
    if packet_info['last_packet'] == 1:
        final_packet = create_packet(CMD_IMAGE_RECEIVED)
        handler.send(final_packet)
        handler.image_handler.save_image_to_disk(handler.sort_image_array(), 'latest_image.jpeg')
        # handler.disconnect()
        return 1
