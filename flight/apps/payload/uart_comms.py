# Low-Level Communication layer - UART

from apps.payload.communication import PayloadCommunicationInterface
from core import logger
from hal.configuration import SATELLITE


class PayloadUART(PayloadCommunicationInterface):
    _connected = False
    _uart = None

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
    def send(cls, pckt, max_packet_size=609):
        if not cls._connected:
            logger.error("Attempted to send data over UART when not connected")
            return

        # check the size to see if we need padding
        # the final size should be 609
        if len(pckt) < max_packet_size:
            pckt += b"\x00" * (max_packet_size - len(pckt))

        logger.debug(f"[PAYLOAD] - Sending packet {pckt[:20]}")
        cls._uart.write(pckt)

    @classmethod
    def read(cls, bytes=609):
        if not cls._connected:
            logger.error("Attempted to read data over UART when not connected")
            return None

        return cls._uart.read(bytes)

    @classmethod
    def is_connected(cls) -> bool:
        return cls._connected
