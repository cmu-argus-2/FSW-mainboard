# Low-Level Communication layer - UART

from apps.payload.communication import PayloadCommunicationInterface
from core import logger
from core.time_processor import TimeProcessor as TPM
from hal.configuration import SATELLITE


class PayloadUART(PayloadCommunicationInterface):
    _connected = False
    _uart = None
    _ACK_PACKET_SIZE = 6  # ACK/NACK: 5 header + 1 status (NO CRC)
    _DATA_PACKET_SIZE = 247  # Data packets: 5 header + 240 data + 2 CRC

    @classmethod
    def connect(cls):
        if SATELLITE.PAYLOADUART_AVAILABLE:
            cls._uart = SATELLITE.PAYLOADUART
            cls._connected = True

            # Flush any stale data in the buffer
            bytes_flushed = cls._uart.in_waiting
            if bytes_flushed > 0:
                # Read and discard stale data
                cls._uart.read(bytes_flushed)
        else:
            cls._uart = None
            cls._connected = False

    @classmethod
    def disconnect(cls):
        cls._connected = False

    @classmethod
    def send(cls, pckt):
        
        # check the size to see if we need padding
        # the final size should be 609
        if len(pckt) < 609:
            pckt += b'\x00' * (609 - len(pckt))
            
        logger.info(f"[PAYLOAD] - Sending packet {pckt}") 
        logger.info(f"[PAYLOAD] -   len:{len(pckt)}") 

        cls._uart.write(pckt)
        
    @classmethod
    def read(cls, bytes=609):
        return cls._uart.read(bytes)

    @classmethod
    def is_connected(cls) -> bool:
        return cls._connected

    @classmethod
    def flush_rx_buffer(cls):
        """Flush the UART receive buffer to clear stale data (like old PING_ACKs)"""
        if cls._connected and cls._uart is not None:
            bytes_flushed = cls._uart.in_waiting
            if bytes_flushed > 0:
                cls._uart.read(bytes_flushed)

    @classmethod
    def packet_available(cls) -> bool:
        """Checks if a complete packet is available to read (6 bytes for ACK, 247 bytes for data)."""
        if not cls._connected or cls._uart is None:
            return False

        bytes_waiting = cls._uart.in_waiting
        # Need at least 6 bytes for minimum packet (ACK)
        return bytes_waiting >= cls._ACK_PACKET_SIZE

    @classmethod
    def get_id(cls):
        """Returns the ID of the UART interface."""
        return 0x20
