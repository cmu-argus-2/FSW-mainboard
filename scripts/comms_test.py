from hal.configuration import SATELLITE

# Forever loop that just transmits to the GS, no receive
while True:
    tx_message = bytes([0xFF, 0x00, 0x01, 0xF0]) + bytearray(240)
    SATELLITE.RADIO.send(tx_message)
    print("Sent message to GS")
