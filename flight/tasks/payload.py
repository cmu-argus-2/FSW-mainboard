# Payload Control Task

from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STATES
from hal.configuration import SATELLITE
import time

PACKET_SIZE = 512       # num bytes
CRC5_SIZE = 1           # num bytes for crc5 (5 bits will be used)

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
    # data_bytes = packet[:-1]  # data minus crc
    # received_crc = packet[-1] >> 3  # crc is the whole byte shifted by 3
    # computed_packet = create_crc5_packet(data_bytes)
    # computed_crc = computed_packet[-1] >> 3  # get only crc
    # return packet == computed_packet
    return True



class MainBoard:
    def __init__(self):
        """Initialize UART"""
        self.uart = SATELLITE.__payload_uart
        
    def receive(self):
        """Receive full packet over UART within 1 second"""
        start_time = time.time()
        packet = bytearray()
        
        # without crc5
        while(True):
            if self.uart.in_waiting:
                packet.extend(self.uart.read(self.uart.in_waiting))
                if len(packet) >= (PACKET_SIZE):  # Ensure full packet received
                    return packet[:(PACKET_SIZE)]  # Only return the first packet size + CRC

    def transmit(self, data):
        """Transmit data over UART within 1 second."""
        if isinstance(data, str):
            data = data.encode()  # Convert string to bytes
            self.uart.write(data)
            time.sleep(0.01)

    def save_to_file(self, data, filename="/sd/output_"+str(time.monotonic())+".jpg"):
        """Save received data to a file"""
        with open(filename, "ab") as f:
            f.write(data)

class Task(TemplateTask):
    def __init__(self, id):
        super().__init__(id)
        self.name = "PAYLOAD"

    async def main_task(self):
        if SM.current_state == STATES.STARTUP:
            pass
        else:
            if not DH.data_process_exists("img"):
                DH.register_image_process()  # WARNING: Image process from DH is different from regular data processes!
            
            # TODO: uart integration
            received_data = self.mainboard.receive()
            
            if received_data:
                if verify_crc5_packet(received_data):
                    self.mainboard.save_to_file(received_data[:-1])  # Save data without CRC
                    self.mainboard.transmit("AACK")  # Send ACK after successful receipt
                else:
                    self.mainboard.transmit("NACK")  # Send NACK if CRC verification fails
            else:
                self.mainboard.transmit("NONE")  # Send NONE if no data was received
           
            # TODO: other commands and logging here
