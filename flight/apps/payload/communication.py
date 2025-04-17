# Low-Level Communication layer


class PayloadCommunicationInterface:
    def __new__(cls, *args, **kwargs):
        if cls is PayloadCommunicationInterface:
            raise TypeError("PayloadComms is a static class and cannot be instantiated.")
        return super().__new__(cls)

    @classmethod
    def connect(cls):
        raise NotImplementedError("Subclass must implement connect()")

    @classmethod
    def disconnect(cls):
        raise NotImplementedError("Subclass must implement disconnect()")

    @classmethod
    def is_connected(cls):
        raise NotImplementedError("Subclass must implement is_connected()")

    @classmethod
    def send(cls, pckt):
        raise NotImplementedError("Subclass must implement send()")

    @classmethod
    def receive(cls):
        raise NotImplementedError("Subclass must implement receive()")

    @classmethod
    def packet_available(cls):
        raise NotImplementedError("Subclass must implement packet_available()")
