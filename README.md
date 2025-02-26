# Flight Software for the Argus Board

The repository contains the current flight software for the **Mainboard** of Argus. Argus is a technology demonstration mission with the goal of demonstrating vision-based Orbit Determination on a low-cost satellite (devoid of any GPS or ground involvement). We also aim to collect a decent dataset of images of the Earth to further efforts in CubeSat visual applications and demonstrate efficient on-orbit ML/GPU processing.

## Architecture 

See [High-Level Architecture](docs/architecture.md)

## Hardware 

The flight software currently supports:
- Argus v1 (ATSAMD51J20)
- Argus v1.1
- Argus v2 (RP2040, in testing)
- Argus v3 (RP2350, in testing)

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

### Troubleshooting 

If the board ever gets stuck in read-only mode, access the REPL and type 
```bash
>>> import storage
>>> storage.erase_filesystem()
```
This will erase and reformat the filesystem.

