import argparse
import filecmp
import os
import platform
import shutil

from build import CPY_VERSION

if platform.system() == "Windows":
    BOARD_PATH = "D:\\"
elif platform.system() == "Linux":
    username = os.getlogin()
    BOARD_PATH = f"/media/{username}/ARGUS"
elif platform.system() == "Darwin":
    BOARD_PATH = "/Volumes/ARGUS"
if platform.node() == "raspberrypi":
    BOARD_PATH = "/mnt/mainboard"


def copy_folder(source_folder, destination_folder, show_identical_files=True):
    for root, dirs, files in os.walk(source_folder):
        for dir in dirs:
            source_dir_path = os.path.join(root, dir)
            relative_dir_path = os.path.relpath(source_dir_path, source_folder)
            destination_dir_path = os.path.join(destination_folder, relative_dir_path)

            if not os.path.exists(destination_dir_path) and CPY_VERSION == 9:
                os.makedirs(destination_dir_path)
                print(f"Created directory {destination_dir_path}")

        for file in files:
            source_path = os.path.join(root, file)
            relative_path = os.path.relpath(source_path, source_folder)
            destination_path = os.path.join(destination_folder, relative_path)

            if not os.path.exists(os.path.dirname(destination_path)):
                os.makedirs(os.path.dirname(destination_path))

            if not os.path.exists(destination_path):
                shutil.copy2(source_path, destination_path)
                print(f"Copied {source_path} to {destination_path}")
            else:
                if filecmp.cmp(source_path, destination_path):
                    if show_identical_files:
                        print(f"File {source_path} already exists and is identical.")
                else:
                    shutil.copy2(source_path, destination_path)
                    print(f"Overwrote {destination_path} with {source_path}")

    # Delete files in destination folder that are not in the new copy
    for root, dirs, files in os.walk(destination_folder):
        for file in files:
            destination_path = os.path.join(root, file)
            relative_path = os.path.relpath(destination_path, destination_folder)
            source_path = os.path.join(source_folder, relative_path)

            """if not os.path.exists(source_path):
                os.remove(destination_path)
                print(f"Deleted {destination_path}")"""


if __name__ == "__main__":
    if platform.system() == "Windows":
        BOARD_PATH = "D:\\"
    elif platform.system() == "Linux":
        username = os.getlogin()
        BOARD_PATH = f"/media/{username}/ARGUS"
        print(BOARD_PATH)
    elif platform.system() == "Darwin":
        BOARD_PATH = "/Volumes/ARGUS"
    if platform.node() == "raspberrypi":
        BOARD_PATH = "/mnt/mainboard"

    # Parses command line arguments.
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-s",
        "--source_folder",
        type=str,
        default="build",
        help="Source folder path",
        required=False,
    )
    parser.add_argument(
        "-d",
        "--destination_folder",
        type=str,
        default=BOARD_PATH,
        help="Destination folder path",
        required=False,
    )
    args = parser.parse_args()

    source_folder = args.source_folder
    destination_folder = args.destination_folder

    print("SOURCE FOLDER: ", source_folder)
    print("DESTINATION FOLDER: ", destination_folder)
    if not os.path.exists(destination_folder):
        print(f"Error: Destination folder '{destination_folder}' does not exist. Is the board connected?")
        exit(1)

    copy_folder(source_folder, destination_folder, show_identical_files=True)
