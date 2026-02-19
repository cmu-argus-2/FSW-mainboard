"""
Satellite radio class for Argus-1 CubeSat.
Message packing/unpacking for telemetry/file TX
and acknowledgement RX.

Authors: Akshat Sahay, Ibrahima S. Sow, Perrin Tong
"""

from apps.comms.auth import get_auth_key_bytes, verify_authenticated_command
from apps.telemetry.splat.splat.telemetry_codec import unpack
from apps.telemetry.splat.splat.telemetry_helper import format_bytes
from core import logger
from core.satellite_config import comms_config as CONFIG
from hal.configuration import SATELLITE
from micropython import const

# Internal error definitions from driver
_ERR_NONE = const(0)
_ERR_CRC_MISMATCH = const(-7)


class SATELLITE_RADIO:

    ARGUS_CS = CONFIG.ARGUS_ID
    HB_PERIOD = CONFIG.HB_PERIOD

    # Init TM frame for preallocating memory
    tm_frame = bytearray(248)

    rx_message_rssi = 0

    auth_enabled = bool(getattr(CONFIG, "AUTH_ENABLED", False))
    auth_key = get_auth_key_bytes(getattr(CONFIG, "AUTH_KEY_HEX", ""))
    rx_auth_status = "not_checked"

    # counters to help determine comms health and performance
    rx_packet_count = 0  # this are just the valid packets
    failed_unpack_count = 0
    crc_error_count = 0
    undef_error_count = 0
    packet_none_count = 0
    packet_auth_fail_count = 0

    tx_packet_count = 0
    tx_failed_count = 0  # this is because the radio was not available

    """
        Name: set_rx_mode
        Description: Used during task init to make sure that the radio is able to receive messages
        as soon as the comms task starts
    """

    @classmethod
    def set_rx_mode(cls):
        # set the radio into receive mode
        SATELLITE.RADIO.startReceive(0xFFFFFF)
        SATELLITE.RADIO.rx_en.value = True
        SATELLITE.RADIO.tx_en.value = False

    """
        Name: get_rssi
        Description: Get RSSI of received packet
    """

    @classmethod
    def get_rssi(cls):
        # Get state
        return cls.rx_message_rssi

    @classmethod
    def get_auth_status(cls):
        return cls.rx_auth_status

    """
        Name: set_tx_ack
        Description: Set internal TX ACK for GS ACKs
    """

    @classmethod
    def set_tx_message(cls, packet):
        # used for now to remain compatible with the old code and support the new transmit queue
        if type(packet) is not bytes:
            logger.error("[COMMS ERROR] TX packet must be of type bytes")
            return
        cls.tx_message = packet

    """
        Name: data_available
        Description: Check if data is available in FIFO buffer
    """

    @classmethod
    def data_available(cls):
        if SATELLITE.RADIO_AVAILABLE:
            return SATELLITE.RADIO.RX_available()
        else:
            logger.error("[COMMS ERROR] RADIO no longer active on SAT")
            return False

    """
        Name: receive_message
        Description: Receive and unpack message from GS
    """

    @classmethod
    def receive_message(cls):
        # Get packet from radio over SPI
        # Assumes packet is in FIFO buffer

        packet = None
        err = -1  # _ERR_NONE is 0
        cls.rx_auth_status = "not_checked"

        # no need to check if radio is available, it was already checked
        packet, err = SATELLITE.RADIO.recv(len=0, timeout_en=True, timeout_ms=1000)

        # Checks on err returned by driver
        if err == _ERR_CRC_MISMATCH:
            # CRC error, packet likely corrupted
            logger.warning("[COMMS ERROR] CRC error occured on incoming packet")
            cls.crc_error_count += 1
            return None

        elif err != _ERR_NONE:
            # Undefined error, packet should never have gotten to comms task
            logger.error("[COMMS ERROR] Undefined error from radio driver")
            cls.undef_error_count += 1
            return None

        # Check if packet exists
        if packet is None:
            # FIFO buffer does not contain a packet, or packet could not be read for some reason
            cls.packet_none_count += 1
            return None

        # hopefully we have a valid packet at this point
        header = packet[0]   # the first byte of the packet is the sc_cs [TODO] - Change this for the real cs size
        logger.info(f"Received packet with header (sc_cs): {header}")
        packet = packet[1:]  # remove the header from the packet

        if cls.auth_enabled:
            # Authenticated command format:
            # [sc_cs|nonce(4)|mac(32)|msg_id|cmd_id|args_len|args...]
            is_valid, reason, packet = verify_authenticated_command(packet, cls.auth_key)

            if not is_valid:
                logger.warning(f"[COMMS ERROR] Command authentication failed: {reason}")
                cls.packet_auth_fail_count += 1
                return None

            cls.rx_auth_status = "passed"
            logger.info("[COMMS] Command authentication passed")

        # unpack the received packet
        message_object = unpack(packet)  # [TODO] - this should be implemented in middleware
        logger.info(f"Received raw packet: {packet}")
        logger.info(f"Unpacked message object: {message_object}")
        if message_object is None:
            cls.failed_unpack_count += 1
            logger.warning("[COMMS ERROR] Failed to unpack received packet")
            return None

        cls.rx_packet_count += 1

        return message_object

    """
        Name: transmit_message
        Description: Transmit message via the LoRa module
    """

    @classmethod
    def transmit_message(cls):
        """
        The message has already been stored in the class variable tx_message by the comms task
        it will add the satellite cs as the header and transmit the message
        """

        # Add source header to distinguish between spacecraft
        cls.tx_message = bytes([cls.ARGUS_CS]) + cls.tx_message

        logger.info(f"transmitting message: {cls.tx_message}")

        # Send a message to GS
        if SATELLITE.RADIO_AVAILABLE:
            SATELLITE.RADIO.send(cls.tx_message)
            cls.tx_packet_count += 1
            logger.info(f"[COMMS] - Message has been transmitted: {format_bytes(cls.tx_message)}")
            return True
        else:
            logger.error("[COMMS ERROR] RADIO no longer active on SAT")
            cls.tx_failed_count += 1
            return False
