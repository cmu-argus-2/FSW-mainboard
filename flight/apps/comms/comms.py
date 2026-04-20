"""
Satellite radio class for Argus-1 CubeSat.
Message packing/unpacking for telemetry/file TX
and acknowledgement RX.

Authors: Akshat Sahay, Ibrahima S. Sow, Perrin Tong
"""

import microcontroller
from apps.comms.auth import get_auth_key_bytes, verify_authenticated_command
from apps.comms.modes import COMMS_MODE, COMMS_MODE_STR
from apps.digipeater import DigipeaterRxQueue
from apps.telemetry.splat.splat.telemetry_codec import unpack
from apps.telemetry.splat.splat.telemetry_helper import format_bytes
from core import logger
from core.satellite_config import comms_config as CONFIG
from hal.configuration import SATELLITE
from micropython import const

# Internal error definitions from driver
_ERR_NONE = const(0)
_ERR_CRC_MISMATCH = const(-7)

# NVM byte 17 for RF_STOP latch (bytes 0-16 are allocated by HAL)
_RF_STOP_NVM_BYTE = const(17)
_RF_STOP_MAGIC = const(0xA5)  # Distinguishes from uninitialized NVM (0xFF)


class SATELLITE_RADIO:

    ARGUS_CS = CONFIG.ARGUS_ID
    HB_PERIOD = CONFIG.HB_PERIOD
    SC_CALLSIGN = CONFIG.SC_CALLSIGN
    GS_CALLSIGN = CONFIG.GS_CALLSIGN

    # Init TM frame for preallocating memory
    rx_message_rssi = 0

    auth_enabled = bool(getattr(CONFIG, "AUTH_ENABLED", False))
    auth_key = get_auth_key_bytes(getattr(CONFIG, "AUTH_KEY_HEX", ""))

    # counters to help determine comms health and performance
    rx_packet_count = 0  # this are just the valid packets
    failed_unpack_count = 0
    crc_error_count = 0
    undef_error_count = 0
    packet_none_count = 0
    packet_auth_fail_count = 0

    tx_packet_count = 0
    tx_failed_count = 0  # this is because the radio was not available

    # RF_STOP / COMMS mode state
    comms_mode = COMMS_MODE.STANDARD
    rf_stop = False

    digipeater_header = b"\x3c\xff\x01"   # have it here as well to facilitate checking



    @classmethod
    def set_rx_mode(cls):
        """
        Name: set_rx_mode
        Description: Used during task init to make sure that the radio is able to receive messages
        as soon as the comms task starts
        """
        # set the radio into receive mode
        SATELLITE.RADIO.startReceive(0xFFFFFF)
        SATELLITE.RADIO.rx_en.value = True
        SATELLITE.RADIO.tx_en.value = False


    @classmethod
    def get_rssi(cls):
        """
        Name: get_rssi
        Description: Get RSSI of received packet
        """

        return cls.rx_message_rssi

    @classmethod
    def get_comms_mode(cls):
        return cls.comms_mode

    @classmethod
    def set_comms_mode(cls, mode_id):
        """Set COMMS operating mode and update mode latches."""
        if mode_id not in COMMS_MODE.ALL:
            logger.warning(f"[COMMS] Invalid mode id: {mode_id}")
            return False

        cls.comms_mode = mode_id
        cls.rf_stop = mode_id == COMMS_MODE.RF_STOP
        cls._persist_rf_stop_latch(cls.rf_stop)
        logger.warning(f"[COMMS] Mode set to {COMMS_MODE_STR.get(mode_id, mode_id)}")
        return True

    @classmethod
    def _persist_rf_stop_latch(cls, enabled):
        """Persist RF_STOP latch across reboot using NVM flash."""
        try:
            microcontroller.nvm[_RF_STOP_NVM_BYTE] = _RF_STOP_MAGIC if enabled else 0x00
        except Exception as e:
            logger.warning(f"[COMMS] Failed to persist RF_STOP latch to NVM: {e}")

    @classmethod
    def restore_comms_mode_from_persistent_state(cls):
        """Restore RF_STOP latch (if present) after boot."""
        try:
            latched = microcontroller.nvm[_RF_STOP_NVM_BYTE] == _RF_STOP_MAGIC
        except Exception:
            latched = False

        if latched:
            cls.comms_mode = COMMS_MODE.RF_STOP
            cls.rf_stop = True
            logger.warning("[COMMS] Restored RF_STOP mode from NVM latch")
        else:
            cls.comms_mode = COMMS_MODE.STANDARD
            cls.rf_stop = False


    @classmethod
    def data_available(cls):
        """
        Name: data_available
        Description: Check if data is available in FIFO buffer
        """

        if SATELLITE.RADIO_AVAILABLE:
            return SATELLITE.RADIO.RX_available()
        else:
            logger.error("[COMMS ERROR] RADIO no longer active on SAT")
            return False

    @classmethod
    def receive_message(cls):
        """Receive and decode a command from the ground station.

        Raw bytes are pushed to the digipeater queue before any command-layer
        processing so that the digipeater task can independently validate and
        relay AX.25 frames.

        Returns the decoded command object, or None.
        """
        packet = None
        err = -1  # _ERR_NONE is 0

        try:
            packet, err = SATELLITE.RADIO.recv(len=0, timeout_en=True, timeout_ms=1000)

            if err == _ERR_CRC_MISMATCH:
                logger.warning("[COMMS ERROR] CRC error on incoming packet")
                cls.crc_error_count += 1
                return None

            elif err != _ERR_NONE:
                logger.error("[COMMS ERROR] Undefined error from radio driver")
                cls.undef_error_count += 1
                return None

            if packet is None:
                cls.packet_none_count += 1
                return None

            # Store raw bytes and feed digipeater queue before any validation
            if packet[:3] == cls.digipeater_header:
                logger.info(f"Received lora aprs packet {packet[:20]}")
                DigipeaterRxQueue.push_packet(packet)

            if cls.auth_enabled:
                is_valid, reason, packet = verify_authenticated_command(packet, cls.auth_key)
                if not is_valid:
                    logger.warning(f"[COMMS ERROR] Command authentication failed: {reason}")
                    cls.packet_auth_fail_count += 1
                    return None

                logger.info("[COMMS] Command authentication passed")

            callsign, message_object = unpack(packet)
            logger.info(f"Received callsign: {callsign}")
            logger.info(f"Received raw packet: {packet}")
            logger.info(f"Unpacked message object: {message_object}")

            if callsign != cls.GS_CALLSIGN:
                logger.error(f"[COMMS ERROR] Received packet with incorrect callsign: {callsign}")
                return None

            if message_object is None:
                cls.failed_unpack_count += 1
                logger.warning("[COMMS ERROR] Failed to unpack received packet")
                return None

            cls.rx_packet_count += 1
            return message_object
        finally:
            cls.set_rx_mode()

    """
        Name: transmit_message
        Description: Transmit message via the LoRa module
    """

    @classmethod
    def transmit_message(cls, packet):
        """
        it will add the satellite cs as the header and transmit the message
        """

        if cls.rf_stop:
            logger.warning("[COMMS] RF_STOP active: dropping TX request")
            return False

        # Send a message to GS
        if SATELLITE.RADIO_AVAILABLE:
            SATELLITE.RADIO.send(packet)
            cls.tx_packet_count += 1
            logger.info(f"[COMMS] - Message has been transmitted: {format_bytes(packet)}")
            return True
        else:
            logger.error("[COMMS ERROR] RADIO no longer active on SAT")
            cls.tx_failed_count += 1
            return False
