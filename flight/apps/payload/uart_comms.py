# Low-Level Communication layer - UART

from apps.payload.communication import PayloadCommunicationInterface
from hal.configuration import SATELLITE


class PayloadUART(PayloadCommunicationInterface):
    _connected = False
    _uart = None
    _ACK_SIZE = 5  # ACK/NACK packets: 4 header + 1 status (NO CRC)
    _FILE_PACKET_SIZE = 246  # File packets: 4 header + 240 data + 2 CRC

    @classmethod
    def connect(cls):
        if SATELLITE.PAYLOADUART_AVAILABLE:
            cls._uart = SATELLITE.PAYLOADUART
            cls._connected = True

            # Flush any stale data in the buffer
            from core import logger

            bytes_flushed = cls._uart.in_waiting
            if bytes_flushed > 0:
                # Read and discard stale data
                cls._uart.read(bytes_flushed)
                logger.info(f"[DEBUG UART] Flushed {bytes_flushed} stale bytes from UART buffer on connect")
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
        """Read variable-length packet from Jetson with smart header parsing"""
        from core import logger

        # Check if we have at least the header (4 bytes)
        if not cls._connected or cls._uart is None:
            return bytearray()

        if cls._uart.in_waiting < 4:
            return bytearray()

        # Read header to determine packet type
        header = cls._uart.read(4)

        # Check for all-zero header (stale data) and flush it
        if all(b == 0 for b in header):
            logger.warning(f"[DEBUG UART] Detected all-zero header, flushing buffer ({cls._uart.in_waiting} bytes remaining)")
            if cls._uart.in_waiting > 0:
                cls._uart.read(cls._uart.in_waiting)
            return bytearray()

        cmd_id = header[0]
        seq_count = (header[1] << 8) | header[2]
        data_len = header[3]

        logger.info(f"[DEBUG UART] Header: cmd={cmd_id:02x}, seq={seq_count}, data_len={data_len}")

        # Determine remaining bytes based on packet type
        # ACK: 4 header + 1 status = 5 bytes (no CRC)
        # File: 4 header + 240 data + 2 CRC = 246 bytes
        if data_len == 1:
            remaining_bytes = 1  # ACK - just status byte
        else:
            remaining_bytes = data_len + 2  # File packet - data + CRC

        # Wait for the rest of the packet to arrive (with timeout)
        # At 115200 baud: 246 bytes takes ~21ms, use 50ms timeout for safety
        import time as TPM

        timeout = 0.05  # 50ms
        start_time = TPM.monotonic()

        while cls._uart.in_waiting < remaining_bytes:
            if TPM.monotonic() - start_time > timeout:
                logger.error(
                    f"[DEBUG UART] Timeout waiting for packet body: need {remaining_bytes} bytes, have {cls._uart.in_waiting}"
                )
                return bytearray()
            TPM.sleep(0.001)  # Sleep 1ms between checks

        # Read the rest of the packet
        rest = cls._uart.read(remaining_bytes)
        if len(rest) < remaining_bytes:
            logger.error(f"[DEBUG UART] Failed to read complete packet body: expected {remaining_bytes}, got {len(rest)}")
            return bytearray()

        # Combine into complete packet
        packet = header + rest
        total_len = len(packet)

        # Log packet info
        hex_str = " ".join(f"{b:02x}" for b in packet[: min(20, total_len)])
        logger.info(f"[DEBUG UART] Received {total_len} bytes: {hex_str}")

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
                from core import logger

                logger.info(f"[DEBUG UART] Flushed {bytes_flushed} stale bytes from RX buffer")

    @classmethod
    def packet_available(cls) -> bool:
        """Checks if a complete 246-byte packet is available to read."""
        if not cls._connected or cls._uart is None:
            return False

        bytes_waiting = cls._uart.in_waiting
        from core import logger

        if bytes_waiting > 0:
            logger.info(f"[DEBUG UART] Bytes in buffer: {bytes_waiting}, need {cls._PACKET_SIZE}")

        return bytes_waiting >= cls._PACKET_SIZE

    @classmethod
    def get_id(cls):
        """Returns the ID of the UART interface."""
        return 0x20
