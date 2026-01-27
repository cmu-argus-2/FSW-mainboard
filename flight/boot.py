import storage
import usb_cdc

# Disable CIRCUITPY drive
storage.disable_usb_drive()

# Enable serial console
usb_cdc.enable(console=True, data=False)

print("MASS STORAGE DISABLED, SERIAL ENABLED")