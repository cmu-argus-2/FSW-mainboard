from busio import UART
import time

ser =  busio.UART('/dev/ttyTHS1', 115200, timeout=1)

time.sleep(2)

ser.write(b"Hello world\n")
print("Sent message to device")

while True:
    received = ser.read()
    print(f"Received: {received.decode('utf-8').strip()}")

