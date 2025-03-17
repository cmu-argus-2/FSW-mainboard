"""
Low-Level Communication layer - Named Pipe (FIFO)"

This is the low-level communication layer for the Payload process using named pipes (FIFO).
This is used in lieu of of UART for Software-in-the-Loop (SIL) testing and local test
scripts (on the host device) with the Payload.

Author: Ibrahima Sory Sow
"""

import os
import select

from communication import PayloadCommunicationInterface

# Named pipe paths (make sure this corresponds to the CMAKE compile definitions)
FIFO_IN = "/tmp/payload_fifo_in"  # Payload reads from this, external process writes to it
FIFO_OUT = "/tmp/payload_fifo_out"  # Payload writes to this, external process reads from it


class PayloadIPC(PayloadCommunicationInterface):  # needed for local testing and SIL
    _connected = False
    _pckt_available = False
    _pipe_in = None  # File descriptor for writing
    _pipe_out = None  # File descriptor for reading

    @classmethod
    def connect(cls):
        """Establishes a connection using named pipes (FIFO)."""
        if cls._connected:
            return

        # Ensure FIFOs exist
        for fifo in [FIFO_IN, FIFO_OUT]:
            if not os.path.exists(fifo):
                try:
                    os.mkfifo(fifo, 0o666)
                except OSError as e:
                    print(f"Error creating FIFO {fifo}: {e}")
                    return

        # Open FIFOs
        try:
            cls._pipe_in = open(FIFO_IN, "w", buffering=1)  # Line-buffered write
            cls._pipe_out = os.open(FIFO_OUT, os.O_RDONLY | os.O_NONBLOCK)  # Non-blocking read
            cls._connected = True
            print("[INFO] PayloadIPC connected.")
        except OSError as e:
            print(f"[ERROR] Failed to open FIFOs: {e}")
            cls.disconnect()

    @classmethod
    def disconnect(cls):
        """Closes the named pipe connections."""
        if not cls._connected:
            return

        if cls._pipe_in:
            cls._pipe_in.close()
            cls._pipe_in = None

        if cls._pipe_out:
            os.close(cls._pipe_out)
            cls._pipe_out = None

        cls._connected = False
        print("[INFO] PayloadIPC disconnected.")

    @classmethod
    def send(cls, pckt: bytearray):
        """Sends a packet (bytearray) via the named pipe."""
        if not cls._connected or cls._pipe_in is None:
            print("[ERROR] Attempt to send while not connected.")
            return False

        try:
            # NOTE: this is just for ease of piping data. The Payload in this mode decode the string to bytes
            # and the actual UART communication is done with raw bytes
            # Convert each byte to its integer string representation and join with spaces
            byte_str = " ".join(str(b) for b in pckt) + "\n"  # append newline for FIFO compatibility

            cls._pipe_in.write(byte_str)
            cls._pipe_in.flush()

            return True
        except OSError as e:
            print(f"[ERROR] Failed to write to FIFO: {e}")
            return False

    @classmethod
    def receive(cls) -> bytearray:
        """Receives a packet from the named pipe (FIFO_OUT)."""
        if not cls._connected or cls._pipe_out is None:
            print("[ERROR] Attempt to receive while not connected.")
            return b""

        try:
            rlist, _, _ = select.select([cls._pipe_out], [], [], 0.5)  # 500ms timeout
            if cls._pipe_out in rlist:
                data = os.read(cls._pipe_out, 512).strip()  # Read from FIFO
                if data:
                    try:
                        # NOTE: This handling is only for the specific IPC. The actual UART communication
                        # is done with raw bytes
                        # Decode bytes to string and split into space-separated values
                        ascii_str = data.decode().strip()
                        num_list = ascii_str.split()  # Split by spaces

                        # Convert each ASCII number string to an integer byte
                        byte_values = bytearray(int(num) for num in num_list)

                        return byte_values
                    except ValueError:
                        print(f"[ERROR] Invalid ASCII numeric data received: {data}")
        except OSError as e:
            print(f"[ERROR] Failed to read from FIFO: {e}")

        return bytearray()  # No data available

    @classmethod
    def is_connected(cls) -> bool:
        return cls._connected

    @classmethod
    def packet_available(cls) -> bool:
        """Checks if a packet is available to read."""
        if not cls._connected or cls._pipe_out is None:
            return False

        try:
            rlist, _, _ = select.select([cls._pipe_out], [], [], 0)  # Non-blocking
            return cls._pipe_out in rlist
        except OSError as e:
            print(f"[ERROR] Failed to check FIFO: {e}")
            return False


if __name__ == "__main__":

    import time

    # Test script for Payload comms

    PayloadIPC.connect()

    if PayloadIPC.is_connected():
        print("Connected.")

    PayloadIPC.send(bytearray([0x03]))  # Request telemetry data
    # PayloadIPC.send(bytearray([0x07,0x01, 0x00, 0x02, 0x00, 0x05])) # Request data capture every 2sec for 5 samples

    time.sleep(0.5)

    # check if packet is available
    if PayloadIPC.packet_available():
        print("Packet available.")

    response = PayloadIPC.receive()
    if response:
        print(f"Received: {response.decode()}")

    PayloadIPC.disconnect()
