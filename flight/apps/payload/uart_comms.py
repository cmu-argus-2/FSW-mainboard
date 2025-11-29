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
        cls._uart.write(pckt)

    @classmethod
    def receive(cls):
        """Read packets from Jetson - ACKs are 6 bytes, data packets are 247 bytes"""
        if not cls._connected or cls._uart is None:
            return bytearray()

        # Need at least 6 bytes to read full ACK packet
        if cls._uart.in_waiting < 6:
            return bytearray()

        # Read 5-byte header first
        header = cls._uart.read(5)

        # Check for all-zero header (stale data) and flush buffer
        if all(b == 0 for b in header):
            if cls._uart.in_waiting > 0:
                cls._uart.read(cls._uart.in_waiting)
            return bytearray()

        # Parse header
        data_len = (header[3] << 8) | header[4]

        # Determine packet type based on data_len
        if data_len == 1:
            # This is an ACK/NACK - total 6 bytes (5 header + 1 status)
            # Read the 1 status byte
            status_byte = cls._uart.read(1)
            if len(status_byte) != 1:
                logger.error("[DEBUG UART] Failed to read ACK status byte")
                return bytearray()

            packet = header + status_byte
            return packet
        else:
            # This is a data packet - need to read remaining bytes to complete 247-byte packet
            # Already have 5 bytes (header), need 242 more (240 data + 2 CRC)
            remaining_bytes = 242

            # Wait for remaining data with timeout
            timeout = 0.05  # 50ms
            start_time = TPM.monotonic()

            while cls._uart.in_waiting < remaining_bytes:
                if TPM.monotonic() - start_time > timeout:
                    logger.error(
                        f"[DEBUG UART] Timeout waiting for data packet body: need {remaining_bytes} bytes, have {cls._uart.in_waiting}"  # noqa: E501
                    )
                    return bytearray()
                TPM.sleep(0.001)

            # Read the rest of the packet
            rest = cls._uart.read(remaining_bytes)
            if len(rest) != remaining_bytes:
                logger.error(f"[DEBUG UART] Failed to read complete data packet: expected {remaining_bytes}, got {len(rest)}")
                return bytearray()

            # Combine into complete 247-byte packet
            packet = header + rest
            return packet

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
