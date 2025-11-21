#!/bin/bash

# Detect the operating system
OS=$(uname -s)
export ARGUS_ROOT=$(pwd)

# Set the correct mpy-cross executable based on the OS
if [ "$OS" == "Linux" ]; then
    MPY_EXEC="mpy-cross"
elif [ "$OS" == "Darwin" ]; then
    MPY_EXEC="mpy-cross-macos"
elif [[ "$OS" == *_NT* ]]; then
    MPY_EXEC="mpy-cross"
else
    echo "Unsupported OS: $OS"
    exit 1
fi

# Make the correct mpy-cross executable
if [[ ! "$OS" == *_NT* ]]; then 
    chmod +x build_tools/$MPY_EXEC

    echo "$MPY_EXEC is now executable"
fi

# Detect the appropriate Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Python is not installed or not found in PATH."
    exit 1
fi

echo "Using Python command: $PYTHON_CMD"

export ARGUS_SIMULATION_FLAG=0

# Check for flight flag
FLIGHT_FLAG=""
if [[ " $@ " =~ " flight " ]]; then
    FLIGHT_FLAG="--flight"
    echo "Using flight configuration (flight.yaml)"
else
    echo "Using ground configuration (ground.yaml)"
fi

if [[ -z $1 ]]; then
    $PYTHON_CMD build_tools/build.py $FLIGHT_FLAG
    $PYTHON_CMD build_tools/move_to_board.py
elif [ "$1" == "emulate" ]; then
    $PYTHON_CMD build_tools/build-emulator.py $FLIGHT_FLAG
    cd build/ && $PYTHON_CMD main.py
    cd -
elif [ "$1" == "emulate-profile" ]; then
    $PYTHON_CMD build_tools/build-emulator.py $FLIGHT_FLAG
    cd build/ && mprof run --python main.py
    mprof plot -o output.png
    cd -
elif [ "$1" == "simulate" ]; then
    export ARGUS_SIMULATION_FLAG=1
    export SIM_REAL_SPEEDUP=275
    echo "ARGUS_SIMULATION_FLAG set to 1 for simulation mode."
    if [[ -z $2 ]]; then
        echo "Running simulation with random trial number."
    elif [[ -z $3 ]]; then
        export ARGUS_SIMULATION_TRIAL=$2
        echo "Running simulation with trial number $2"
    elif [[ -z $4 ]]; then
        export ARGUS_SIMULATION_TRIAL=$2
        export ARGUS_SIMULATION_DATE=$3
        echo "Running simulation with trial number $2 at date $3"
    else
        export ARGUS_SIMULATION_TRIAL=$2
        export ARGUS_SIMULATION_DATE=$3
        export ARGUS_SIMULATION_SET_NAME=$4
        echo "Running simulation from set $4 with trial number $2 at date $3"
    fi
    $PYTHON_CMD build_tools/build-emulator.py $FLIGHT_FLAG
    cd build/ && rm -rf sd && $PYTHON_CMD main.py
    cd -
elif [ "$1" == "flight" ]; then
    # If --flight is the only argument, build with flight config
    $PYTHON_CMD build_tools/build.py $FLIGHT_FLAG
    $PYTHON_CMD build_tools/move_to_board.py
else
    # Pass flight flag to build command
    $PYTHON_CMD build_tools/build.py $FLIGHT_FLAG
    $PYTHON_CMD build_tools/move_to_board.py -d "$1"
fi
