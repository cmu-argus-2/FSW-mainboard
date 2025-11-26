# Low-Level Communication layer - UART

from apps.payload.communication import PayloadCommunicationInterface
from hal.configuration import SATELLITE


class PayloadUART(PayloadCommunicationInterface):
    _connected = False
    _uart = None
    _PCKT_SIZE = 250  # USED TO BE 250

    @classmethod
    def connect(cls):
        if SATELLITE.PAYLOADUART_AVAILABLE:
            cls._uart = SATELLITE.PAYLOADUART
            cls._connected = True
        else:
            cls._uart = None
            cls._connected = False

    @classmethod
    def disconnect(cls):
        cls._connected = False

    @classmethod
    def send(cls, pckt):
        cls._uart.write(pckt)

    @classmethod
    def receive(cls):
        if cls.packet_available():
            pckt = cls._uart.read(cls._PCKT_SIZE)
            return pckt
        return bytearray()

    @classmethod
    def is_connected(cls) -> bool:
        return cls._connected

    @classmethod
    def packet_available(cls) -> bool:
        """Checks if a packet is available to read."""
        if not cls._connected or cls._uart is None:
            return False
        return cls._uart.in_waiting >= 0

    @classmethod
    def get_id(cls):
        """Returns the ID of the UART interface."""
        return 0x20
