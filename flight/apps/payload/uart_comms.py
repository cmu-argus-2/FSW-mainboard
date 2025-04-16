# Low-Level Communication layer - UART

from apps.payload.communication import PayloadCommunicationInterface
from hal.configuration import SATELLITE


class PayloadUART(PayloadCommunicationInterface):
    _connected = False
    _pckt_available = False
    _uart = None

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
        pass

    @classmethod
    def receive(cls):
        pass
