"""
Build script for Argus
This script is only used for compiling .py files to .mpy files
"""

import argparse
import os
import platform
import shutil
import sys

system = platform.system()


def get_board_path():
    if system == "Windows":
        BOARD_PATH = "D:\\"
    elif system == "Linux":
        username = os.getlogin()
        BOARD_PATH = f"/media/{username}/ARGUS"
    elif system == "Darwin":
        BOARD_PATH = "/Volumes/ARGUS"
    elif platform.node() == "raspberrypi":
        BOARD_PATH = "/mnt/mainboard"
    return BOARD_PATH


def get_circuitpython_version(BOARD_PATH):
    with open(os.path.join(BOARD_PATH, "boot_out.txt")) as boot:
        circuit_python, _ = boot.read().split(";")
    return int(circuit_python.split(" ")[-3][0])


def get_board_id(BOARD_PATH):
    with open(os.path.join(BOARD_PATH, "boot_out.txt")) as boot:
        lines = boot.readlines()
        if len(lines) > 1:
            second_line = lines[1].strip()
            board_id = second_line.split(":")[1].strip()
            return board_id
    # Default to compiling for Argus
    return "Argus"


def get_commit_hash():
    try:
        commit_hash = os.popen("git rev-parse HEAD").read().strip()
        return commit_hash
    except Exception as e:
        print(f"Error getting commit hash: {e}")
        return None


def get_branch_name():
    try:
        branch_name = os.popen("git rev-parse --abbrev-ref HEAD").read().strip()
        return branch_name
    except Exception as e:
        print(f"Error getting branch name: {e}")
        return None


BOARD_PATH = get_board_path()
CPY_VERSION = 8  # Default to CPY 8
BOARD_ID = "Argus"  # Default to compiling for Argus
if os.path.exists(BOARD_PATH):
    CPY_VERSION = get_circuitpython_version(BOARD_PATH)
    BOARD_ID = get_board_id(BOARD_PATH)
GIT_BRANCH = get_branch_name()
GIT_COMMIT = get_commit_hash()

MPY_CROSS_NAME = "mpy-cross-cpy9" if CPY_VERSION == 9 else "mpy-cross"
if system == "Darwin":
    MPY_CROSS_NAME = "mpy-cross-macos-cpy9" if CPY_VERSION == 9 else "mpy-cross-macos"
if platform.node() == "raspberrypi":
    MPY_CROSS_NAME = "mpy-cross-rpi"
MPY_CROSS_PATH = f"{os.getcwd()}/build_tools/{MPY_CROSS_NAME}"

if system == "Windows":
    MPY_CROSS_PATH = shutil.which("mpy-cross")
    if MPY_CROSS_PATH:
        print(f"mpy-cross found at {MPY_CROSS_PATH}")
    else:
        print("mpy-cross not found, please install with 'pip install mpy_cross'")
        sys.exit(-1)


def check_directory_location(source_folder):
    if not os.path.exists(MPY_CROSS_PATH):
        raise FileNotFoundError(f"MPY_CROSS_PATH folder {MPY_CROSS_PATH} not found")

    if not os.path.exists(f"{source_folder}"):
        raise FileNotFoundError(f"Source folder {source_folder} not found")


def create_build(source_folder):
    build_folder = "build/"
    if os.path.exists(build_folder):
        shutil.rmtree(build_folder)

    build_folder = os.path.join(build_folder, "lib/")

    os.makedirs(build_folder)

    for root, _, files in os.walk(source_folder):
        # only include drivers or drivers_PYC_V05
        if BOARD_ID.startswith("Argus") and os.path.relpath(root, source_folder).startswith("hal/drivers_PYC_V05"):
            print(f"Skipping {os.path.relpath(root, source_folder)}")
            continue
        elif BOARD_ID.startswith("PyCubed") and os.path.relpath(root, source_folder).startswith("hal/drivers"):
            print(f"Skipping {os.path.relpath(root, source_folder)}")
            continue

        for file in files:
            if file.endswith(".py") or file.endswith(".mpy"):
                source_path = os.path.join(root, file)

                build_path = os.path.join(build_folder, os.path.relpath(source_path, source_folder))

                os.makedirs(os.path.dirname(build_path), exist_ok=True)
                shutil.copy2(source_path, build_path)
                print(f"Copied {source_path} to {build_path}")

                current_dir = os.getcwd()

                # Change directory to the build path folder
                os.chdir(os.path.dirname(build_path))

                if file == "main.py":
                    # rename main.py to main_module.py
                    os.rename("main.py", "main_module.py")
                    file_name = "main_module.py"
                else:
                    # Extract file name
                    file_name = os.path.basename(file)

                if file_name.endswith(".py"):
                    try:
                        os.system(f"{MPY_CROSS_PATH} {file_name} -O3")
                    except Exception as e:
                        print(f"Error occurred while compiling {file_name}: {str(e)}")

                    # Delete file python file once it has been compiled
                    os.remove(file_name)

                os.chdir(current_dir)

    # Create main.py file with single import statement "import main_module"
    build_folder = os.path.join(build_folder, "..")
    with open(os.path.join(build_folder, "main.py"), "w") as f:
        if GIT_BRANCH:
            f.write(f'print("Branch: {GIT_BRANCH}")\n')
        if GIT_COMMIT:
            f.write(f'print("Commit: {GIT_COMMIT}")\n')
        f.write("import main_module\n")

    # Create SD folder
    os.makedirs(os.path.join(build_folder, "sd/"), exist_ok=True)
    return build_folder


if __name__ == "__main__":
    # Parses command line arguments.
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-s",
        "--source_folder",
        type=str,
        default="flight",
        help="Source folder path",
        required=False,
    )
    args = parser.parse_args()

    source_folder = args.source_folder

    check_directory_location(source_folder)

    if GIT_BRANCH:
        print(f"Branch: {GIT_BRANCH}")
    if GIT_COMMIT:
        print(f"Commit: {GIT_COMMIT}")

    print(f"CircuitPython version: {CPY_VERSION}")
    print(f"Board ID: {BOARD_ID}")

    build_folder = create_build(source_folder)
