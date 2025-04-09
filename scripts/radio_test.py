import time

from hal.configuration import SATELLITE

# Boot up SC
print("Booting ARGUS-1...")
SATELLITE.boot_sequence()
print("ARGUS-1 booted.")
print(f"Boot Errors: {SATELLITE.ERRORS}")

while True:
    # Send a fake message
    tx_msg = bytearray([0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07])
    SATELLITE.RADIO.send(tx_msg)

    start_time = time.time()

    # Listen for 1s
    while time.time() - start_time < 1:
        if SATELLITE.RADIO.RX_available():
            packet, err = SATELLITE.RADIO.recv(len=0, timeout_en=True, timeout_ms=1000)
            print(packet)
            print(SATELLITE.RADIO.rssi())
