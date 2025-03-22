CircuitPython Compilation & Flashing Guide for Argus
=====
## Supported Board CPY Information
| Mainboard  | MCU | CPY  |
| ------------- | ------------- | ------------- |
| Argus 1.0  | ATSAMD51 | 8 |
| Argus 1.1  | ATSAMD51 | 8, 9 |
| Argus 2  | RP2040 | 8, 9 |
| Argus 3  | RP2350 | 9 |
## Compilation
This guide is specific to Argus, for additional information refer to the [official Adafruit CircuitPython Guide](https://learn.adafruit.com/how-to-add-a-new-board-to-circuitpython/get-setup-to-add-your-board)

**1. Setup Environment**

**For CircuitPython 9, you will need to compile on Ubuntu 24.04**

Refer to the [official Adafruit CircuitPython Guide](https://learn.adafruit.com/building-circuitpython/introduction) if you are setting up locally.

CircuitPython has been cloned and avilable to all users on the FSW FlatSat machine (Ubuntu).
Run the following commands to prepare your environment.
```
source /home/Shared/venv/bin/activate # Python Virtual Environment with all necessary libraries
cd /home/Shared/circuitpython
```

**2. Create/Copy Board Definitions**

Board definitions are typically created and stored in the [firmware folder](firmware), under each specific Mainboard's directory. If they are available, download the relevant folders.

Navigate to the relevant port folder
```
# e.g. for Raspberry Pi MCUs
cd ports/raspberrypi/boards
```
For boards that do not have board definitions on the FSW repo, create a copy of a board's folder that is similar to the mainboard, and rename it to ArgusX(X being the version number). If the files are available on FSW repo, simply create the ArgusX folder and place the relevant files in this folder.
This folder should contain the following files:
  1. board.c
     
     This file typically requires little change. If there are pin references, change them to match your specific board.
  2. mpconfigboard.h
     
     This file specifies the board name, MCU name and serial buses. While board name is not important, ensure the MCU name is correct and the serial buses references the correct pins.
  3. mpconfigboard.mk

     This file specifies the USB, chip(MCU), flash, and CircuitPython libraries. While USB information is not important, ensure the chip family, chip variant and flash device are correctly specified. The following CircuitPython libraries should also be installed in firmware to allow FSW to run correctly.
     ```
     CIRCUITPY_ULAB = 1
     FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_BusDevice
     FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_Register
     FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_SD
     ```
     While we can specify the drive name of the flash in firmware with, we have found this doesn't always work.
     ```
     CIRCUITPY_DRIVE_LABEL = "ARGUS"
     ```
  4. pins.c
   
     This file defines the pin names available on the board. Add the relevant name of each GPIO pin for ease of read in FSW.  
  5. There might be other files depending on the port.

**3. Compiling the Firmware**

Navigate one level up (i.e. circuitpython/ports/[vendor]).
Ensure that build-ArgusX folder does not exist in this directory, or else the compilation might fail.
Run the following command to compile the target firmware
```
# ArgusX is the folder name in the boards folder
# -jY is an optional argument, where Y is the number of threads available on your computer
make BOARD=ArgusX -jY
```
If the compilation is successful, a build-ArgusX folder will be be created. A firmware.uf2 file will be created in this folder. Please upload this to the FSW repo and all relevant files for future development.

## Flashing

### Raspberry Pi
To enter bootloader, turn off the board and hold the BOOT button. Drag and drop the uf2 file to the board, it will restart with the new firmware.

### ATSAMD

To enter bootloader, double tap the BOOT button. Drag and drop the uf2 file to the board, it will restart with the new firmware.



