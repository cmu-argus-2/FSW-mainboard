"""

High-level interface to communicate with the RF MCU managing the SEMTECH SX1262 RF LoRa module (E22-900M30S).
It defines the SPI communication protocol between the 2 MCU's.

TODO: Until porting to new board configuration is complete, this will send directly to the radio module.

"""
from core import logger
from hal.configuration import SATELLITE


class RF_MCU:
    """
    High-level interface to communicate with the RF MCU managing the SEMTECH SX1262 RF LoRa module (E22-900M30S).
    """

    SPI = None

    @classmethod
    def transmit(self, msg_bytes: bytearray):
        """
        Transmit data to the RF MCU for transmission.

        Args:
            data (bytes): Data to transmit.
        """
        SATELLITE.RADIO.send(msg_bytes)
        return int(msg_bytes[0])

    @classmethod
    def receive(self):
        """
        Receive data from the RF MCU.

        Returns:
            bytes: Received data.
        """
        pass
