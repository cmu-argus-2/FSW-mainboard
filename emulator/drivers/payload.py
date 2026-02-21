"""Payload driver module."""


class Payload:
    """Payload device driver."""

    def __init__(self) -> None:
        self.baudrate = 460800

    def read(self, bytes_to_read: int) -> bytearray:
        """Read data from the payload."""
        return bytearray()

    def write(self, pckt: bytearray) -> None:
        """Write data to the payload."""
        pass

    @property
    def in_waiting(self) -> int:
        """Return the number of bytes waiting to be read."""
        return 0
