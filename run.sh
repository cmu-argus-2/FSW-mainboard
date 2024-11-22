#!/bin/bash

# Detect the operating system
OS=$(uname -s)

# Set the correct mpy-cross executable based on the OS
if [ "$OS" == "Linux" ]; then
    MPY_EXEC="mpy-cross"
elif [ "$OS" == "Darwin" ]; then
    MPY_EXEC="mpy-cross-macos"
else
    echo "Unsupported OS: $OS"
    exit 1
fi

# Make the correct mpy-cross executable
chmod +x build_tools/$MPY_EXEC

echo "$MPY_EXEC is now executable"

export ARGUS_SIMULATION_FLAG=0

if [[ -z $1 ]];
then
    python3 build_tools/build.py && python3 build_tools/move_to_board.py
elif [ "$1" == "emulate" ];
then
    python3 build_tools/build-emulator.py
    cd build/ && python3 main.py
    cd -
elif [ "$1" == "emulate-profile" ];
then
    python3 build_tools/build-emulator.py
    cd build/ && mprof run --python main.py
    # cd build/ && mprof plot -o output.png && cd ..
    mprof plot -o output.png 
    cd -
elif [ "$1" == "simulate" ];
then
    export ARGUS_SIMULATION_FLAG=1
    export ARGUS_ROOT=$(pwd)
    echo "ARGUS_SIMULATION_FLAG set to 1 for simulation mode."
    python3 build_tools/build-emulator.py
    cd build/ && python3 main.py
    cd -
fi