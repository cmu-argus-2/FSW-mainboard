# Low-Level Communication layer (UART)

_PCKT_BUF_SIZE = 200


class PayloadComms:
    _connected = False
    _pckt_available = False
    _buffer = bytearray(_PCKT_BUF_SIZE)

    def __new__(cls, *args, **kwargs):
        raise TypeError(f"{cls.__name__} is a static class and cannot be instantiated.")

    @classmethod
    def connect(cls):
        raise NotImplementedError("Subclass must implement connect()")

    @classmethod
    def disconnect(cls):
        raise NotImplementedError("Subclass must implement disconnect()")

    @classmethod
    def is_connected(cls):
        return cls._connected

    @classmethod
    def send(cls, pckt):
        raise NotImplementedError("Subclass must implement send()")

    @classmethod
    def receive(cls):
        raise NotImplementedError("Subclass must implement receive()")

    @classmethod
    def packet_available(cls):
        return cls._pckt_available


class PayloadCommsUART(PayloadComms):
    _connected = False
    _pckt_available = False

    @classmethod
    def connect(cls):
        cls._connected = True

    @classmethod
    def disconnect(cls):
        cls._connected = False

    @classmethod
    def send(cls, pckt):
        pass

    @classmethod
    def receive(cls):
        pass


class PayloadCommsIPC(PayloadComms):  # needed for local testing and SIL
    _connected = False
    _pckt_available = False

    @classmethod
    def connect(cls):
        cls._connected = True

    @classmethod
    def disconnect(cls):
        cls._connected = False

    @classmethod
    def send(cls, pckt):
        pass

    @classmethod
    def receive(cls):
        pass
