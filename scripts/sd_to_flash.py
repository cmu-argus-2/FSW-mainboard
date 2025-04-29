import os
import time

import storage
from core.data_handler import join_path, path_exist
from hal.configuration import SATELLITE

print("Booting ARGUS...")
SATELLITE.boot_sequence()
print("ARGUS booted.")
print(f"Boot Errors: {SATELLITE.ERRORS}")


def get_dirname(path):
    if "/" not in path:
        return ""
    return path.rsplit("/", 1)[0]


def get_relpath(path, start):
    if not path.startswith(start):
        raise ValueError(f"Path '{path}' does not start with '{start}'")
    return path[len(start) :].lstrip("/")


def move_files_to_flash(path="/sd", source_base="/sd", destination_base="/log"):
    try:
        if not path_exist(destination_base):
            os.mkdir(destination_base)

        for file_name in os.listdir(path):
            if file_name.startswith("."):
                continue

            file_path = join_path(path, file_name)
            relative_path = get_relpath(file_path, source_base)
            destination_path = join_path(destination_base, relative_path)

            if os.stat(file_path)[0] & 0x8000:
                destination_dir = get_dirname(destination_path)
                if not path_exist(destination_dir):
                    os.mkdir(destination_dir)
                print(f"Copying {file_path} to {destination_path}")
                with open(file_path, "rb") as src_file:
                    with open(destination_path, "wb") as dest_file:
                        dest_file.write(src_file.read())
            elif os.stat(file_path)[0] & 0x4000:
                move_files_to_flash(file_path, source_base, destination_base)

    except Exception as e:
        print(f"Error moving files: {e}")


while True:
    try:
        SATELLITE.NEOPIXEL.fill([255, 0, 0])
        storage.remount("/", readonly=False)
        SATELLITE.NEOPIXEL.fill([0, 0, 255])
        move_files_to_flash()
        print("Copy complete.")
        SATELLITE.NEOPIXEL.fill([0, 255, 0])
        storage.remount("/", readonly=True)
        break
    except Exception as e:
        print(f"Error: {e}")
        print("Eject ARGUS, retrying in 5 seconds...")
        time.sleep(5)

print("Power cycle the board to complete the process.")
