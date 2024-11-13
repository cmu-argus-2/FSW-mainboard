import time

from apps.comms.comms import SATELLITE_RADIO
from hal.configuration import SATELLITE

print("Booting ARGUS-1...")
boot_errors = SATELLITE.boot_sequence()
print("ARGUS-1 booted.")
print(f"Boot Errors: {boot_errors}")

## ---------- MAIN CODE STARTS HERE! ---------- ##

while True:
    if SATELLITE.RADIO is not None:
        SATELLITE_RADIO.set_tm_frame(bytes([0x01, 0x00, 0x00, 0x04, 0xFF, 0xEE, 0xDD, 0xCC]))
        tx_msg_id = SATELLITE_RADIO.transmit_message()
        print(f"Sent {tx_msg_id}")
        time.sleep(5)

    if SATELLITE.RADIO is not None:
        rq_msg_id = SATELLITE_RADIO.receive_message()
        print(f"RQ'd {rq_msg_id}")
        time.sleep(5)
