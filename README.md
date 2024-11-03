# Flight Software for the PyCubed Board (Argus-1)

The repository contains the current flight software stack for the **Mainboard** of Argus-1. Argus-1 is a technology demonstration mission with the goal of:
- Demonstrating Vision-based Orbit Determination (A&OD) on a low-cost satellite (devoid of any GPS or ground involvement)
- Collecting a dataset of images of the Earth to further efforts in CubeSat visual applications.
- Demonstrating efficient on-orbit ML/GPU Payload processing 

## Build and Execution

### With mainboard

Building current files and moving them to the board can be handled by the run.sh script which can be run via:
```bash
./run.sh
```
The script first builds and compiles the flight software files to .mpy files and transfers them to the mainboard you are connected to.

### Without mainboard

In the absence of the mainboard, you should either run the simulator or emulator.

To run the emulator:
```bash
./run.sh emulate
```

To run the simulator:
```bash
./run.sh simulate
```

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


