import gc
import sys
import time

from core import logger, setup_logger, state_manager
from hal.configuration import SATELLITE

from apps.comms.comms import SATELLITE_RADIO
from micropython import const
from hal.cubesat import Device

ASIL4 = const(4)



# Memory stats
def print_memory_stats(call_gc=True):
    if call_gc:
        gc.collect()
    print(f"Memory stats after gc: {call_gc}")
    print(f"Total memory: {str(gc.mem_alloc() + gc.mem_free())} bytes")
    print(f"Memory free: {str(gc.mem_free())} bytes")
    print(f"Memory used: {int((gc.mem_alloc() / (gc.mem_alloc() + gc.mem_free())) * 100)}%")


for path in ["/hal", "/apps", "/core"]:
    if path not in sys.path:
        sys.path.append(path)

setup_logger(level="INFO")

print_memory_stats(call_gc=True)

# print("Booting ARGUS...")
# # this will start each one of the devices
# SATELLITE.boot_sequence()
# print("ARGUS booted.")
# print(f"Boot Errors: {SATELLITE.ERRORS}")

# lets init only the radio
radio_device = Device(SATELLITE.__radio_boot, ASIL4, peripheral_line=False)
SATELLITE.__boot_device("RADIO",  radio_device)
SATELLITE.__device_list["RADIO"].device = radio_device.device
print(f"Boot Errors: {radio_device.error}")

print("Waiting 1 sec...")
time.sleep(1)

# transmit a simple message to indicate that the satellite has started
tx_msg_id =  SATELLITE_RADIO.transmit_message()
print(f"Transmitted message with ID: {tx_msg_id}")


# start listening for messages
print("Starting RX mode...")
tx_counter = 0
while True:
    if SATELLITE_RADIO.data_available():
        if SATELLITE.RADIO_AVAILABLE:
            
            # get the packet
            packet, err = SATELLITE.RADIO.recv(len=0, timeout_en=True, timeout_ms=1000)
            
            # get the rssi and snr of the packet
            rssi = SATELLITE.RADIO.rssi()  # this is the value for the last received packet
            snr = SATELLITE.RADIO.snr()    # this is the value for the last received packet
            
            print(f"Received packet: {packet}")
            print(f"Received error: {err}")
            print(f"Received RSSI: {rssi}")
            print(f"Received SNR: {snr}")
            
            time.sleep(2)
            
            # echo back the packet
            _, state = SATELLITE.RADIO.send(packet)
            if state != 0:
                print(f"Failed to echo back message, state: {state}")
            tx_counter += 1
            print(f"Echoed back message with ID: {tx_counter}")

        



# lets implement a simple echo server with the lora module
# will respond to any received packet with the same data
