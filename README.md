# Flight Software for the Argus Board

**This page is deprecated and no longer maintained. Please refer to [Confluence](https://spacecraft.atlassian.net/wiki/spaces/CMA/pages/15761570/FSW+Overview) for internal docs.

The repository contains the current flight software for the **Mainboard** of Argus. Argus is a technology demonstration mission with the goal of demonstrating vision-based Orbit Determination on a low-cost satellite (devoid of any GPS or ground involvement). We also aim to collect a decent dataset of images of the Earth to further efforts in CubeSat visual applications and demonstrate efficient on-orbit ML/GPU processing.

## Architecture 

See [High-Level Architecture](docs/architecture.md)

## Hardware 

The flight software currently supports:
- Argus v1 (ATSAMD51J20)
- Argus v1.1 (ATSAMD51J20)
- Argus v2 (RP2040)
- Argus v3 (RP2350)

## Installation
NOTE : The simulation only supports Ubuntu systems with a version >= 22.04
```bash
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
git submodule init
git submodule update
sh install.sh
```

## Build and Execution

### With mainboard

Building current files and moving them to the board can be handled by the run.sh script which can be run via:
```bash
./run.sh
```
The script first builds and compiles the flight software files to .mpy files and transfers them to the mainboard you are connected to. The compilation is supported on Linux, MacOS, Windows, and RPi.

### Without mainboard

In the absence of the mainboard, you should either run the simulator or emulator.

To run the emulator:
```bash
source .venv/bin/activate
./run.sh emulate
```

To run the simulator:
```bash
source .venv/bin/activate
./run.sh simulate
```

Virtual Environment prevents any dependency conflicts with your global filesystem

### Build or move 

For only building files or moving them to the board as individual actions, you can use the automated scripts, build.py and move_to_board.py, in the build_tools directory. Note that move_to_board.py automatically updates all changes (including adding and deleting files) on the target board.

To build:
```bash
python3 build_tools/build.py
```
or for emulation
```bash
python3 build_tools/build-emulator.py
```

To move to board:
```bash
python move_to_board.py -s <source_folder_path> -d <destination_folder_path>
```

## Common Problems

### Board Stuck in Read-Only Mode

If the board ever gets stuck in read-only mode, access REPL and type 
```bash
>>> import storage
>>> storage.erase_filesystem()
```
This will erase and reformat the filesystem.

### Reflashing the board

If you have access to the buttons on the board, you can enter the bootloader using buttons on-board, refer to the [firmware guide](firmware/README.md)
If you do not have access to the buttons, access REPL and type
```bash
>>> import microcontroller
>>> microcontroller.on_next_reset(microcontroller.RunMode.UF2)
>>> microcontroller.reset()
```
**DO NOT RUN THIS AS YOUR MAIN.PY, YOUR BOARD WILL GET STUCK IN A LOOP AND CAN'T GET OUT OF BOOTLOADER.**

### Nuking the board

If you unfortunately get your board stuck in bootloader, or cannot explain why the board is behaving weird. As the last resort, you can "nuke" the board by flashing it with the nuke firmwares. "Nuke" firmware are in the firmware folder, make sure you use the correct nuke for the MCU. Refer to the [firmware guide](firmware/README.md) for how to flash.

### Can't compile and move the code to the board
If you see the message "Error: Destination folder '{destination_folder}' does not exist. Is the board connected?" There are a few possiblities:
1) Make sure your board is powered. If you are powering through USB. Make sure VSYS and GND pins or the high and low side inhibitors are jumped.
2) Is the board correctly named as ARGUS? New boards are defaulted as CIRCUITPY, rename it using your system tools and reconnect it to your computer.
3) Check the USB connector on the mainboard.

### Data Handler keeps complaining
The data structure of the task might have changed. Wiping the SD Card using the script should solve the problem.

### Mainboard keeps restarting (brown out) randomly
If you are using USB to power your board, consider turning off some devices. Radio will not be able to run without power supply. 
Other common devices causing brown out are burn wires, consider lowering its strength appropriately.

### Do I have to change anything before compiling the code for my targetted board.
No. Configurations are automatically detected.

