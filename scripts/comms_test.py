from hal.configuration import SATELLITE

print()
print("Booting ARGUS-1...")
boot_errors = SATELLITE.boot_sequence()
print("ARGUS-1 booted.")
print(f"Boot Errors: {boot_errors}")

# Forever loop that just transmits to the GS, no receive
while True:
    tx_message = bytes([0xFF, 0x00, 0x01, 0xC8]) + bytearray(200)
    SATELLITE.RADIO.send(tx_message)
    print("Sent message to GS")
