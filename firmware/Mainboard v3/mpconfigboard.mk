USB_VID = 0x2E8A
USB_PID = 0x10A3
USB_PRODUCT = "argus3"
USB_MANUFACTURER = "rexlab"

CHIP_VARIANT = RP2350
CHIP_PACKAGE = B
CHIP_FAMILY = rp2

EXTERNAL_FLASH_DEVICES = "W25Q32JVxQ"

CIRCUITPY_DRIVE_LABEL = "ARGUS"
CIRCUITPY__EVE = 1
CIRCUITPY_ULAB = 1

FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_BusDevice
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_Register
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_SD
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_NeoPixel
