# Payload Control Task

import time

from apps.telemetry.constants import PAYLOAD_IDX
from core import TemplateTask
from core import state_manager as SM
from core.data_handler import DataHandler as DH
from core.states import STATES
from hal.configuration import SATELLITE

PACKET_SIZE = 512  # num bytes
CRC5_SIZE = 1  # num bytes for crc5 (5 bits will be used)

class MainBoard:
    def __init__(self):
        """Initialize UART"""
        self.uart = SATELLITE.PAYLOADUART

    def receive(self):
        """Receive full packet over UART within 1 second"""
        start_time = time.time()
        packet = bytearray()

        # without crc5
        while (time.time() - start_time) < 1:
            if self.uart.in_waiting:
                byte = self.uart.read(1)
                if byte:
                    byte = byte[0]
                    packet.append(byte)
                    if len(packet) == PACKET_SIZE:
                        return packet

        return None

    def transmit(self, data):
        """Transmit data over UART within 1 second."""
        if isinstance(data, str):
            data = data.encode()  # Convert string to bytes
            self.uart.write(data)
            time.sleep(0.01)

    def save_to_file(self, data, filename="/sd/output_" + str(time.monotonic()) + ".jpg"):
        """Save received data to a file"""
        with open(filename, "ab") as f:
            f.write(data)


class Task(TemplateTask):
    def __init__(self, id):
        super().__init__(id)
        self.name = "PAYLOAD"
        self.mainboard = MainBoard()

    async def main_task(self):
        if SM.current_state == STATES.STARTUP:
            pass
        else:
            self.log_info("Payload task started")
            if not DH.data_process_exists("img"):
                DH.register_image_process()  # WARNING: Image process from DH is different from regular data processes!
            
            # send a "READY" byte
            self.mainboard.transmit("RDDY")

            # prepare to receive data from jetson
            received_data = self.mainboard.receive()

            if received_data:
                if True:
                    # self.mainboard.save_to_file(received_data[:-1])  # Save data without CRC
                    self.log_info(f"ACK: Received {len(received_data)} bytes")
                    self.mainboard.transmit("AACK")  # Send ACK after successful receipt
                else:
                    self.log_info("NACK: CRC verification failed")
                    self.mainboard.transmit("NACK")  # Send NACK if CRC verification fails
            else:
                self.log_info("No data received")
                self.mainboard.transmit("NONE")  # Send NONE if no data was received

            # TODO: other commands and logging here
