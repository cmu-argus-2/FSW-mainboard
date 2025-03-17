"""
Payload Control Interface

This module defines the Payload Controller class, which is responsible for managing the main interface between
the host and the Payload.

Author: Ibrahima Sory Sow

"""

from definitions import CommandID, ErrorCodes
from protocol import Decoder, Encoder

_PING_VALUE = 0x60


class PayloadTM:  # Simple data structure holder
    pass


class PayloadController:

    communication_interface = None

    @classmethod
    def initialize(cls, communication_interface):
        cls.communication_interface = communication_interface
        cls.communication_interface.connect()

    @classmethod
    def deinitialize(cls):
        cls.communication_interface.disconnect()

    @classmethod
    def ping(cls):
        cls.communication_interface.send(Encoder.encode_ping())

        resp = cls.communication_interface.receive()
        if resp:
            return Decoder.decode(resp) == _PING_VALUE
        return False

    @classmethod
    def shutdown(cls):
        pass
