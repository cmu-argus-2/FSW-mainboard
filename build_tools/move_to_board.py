"""
Move files from build folder to mainboard

this is the file that I will need to update to support mpremote
"""

import argparse
import filecmp
import os
import shutil
import time

from build import get_board_path, get_circuitpython_version

import subprocess

def mpremote_run(*args, check=True, capture_output=False, text=None):
    
    if PORT is None:
        raise ValueError("PORT is not set. Cannot run mpremote command.")
    
    result = subprocess.run(
        ["mpremote", "connect", PORT, *args],
        check=check,
        capture_output=capture_output,
        text=text
    )
    
    return result


def search_port():
    """
    It will run mpremote connect list, search for the board and return its port

    expeted output example:
    '/dev/ttyACM0 3C27AE4A06D29828 2e8a:10a3 rexlab argus4\n'
    
    """
    result = subprocess.run(
        ["mpremote", "connect", "list"],
        capture_output=True,
        text=True,
        check=True
    )
    output = result.stdout
    for line in output.splitlines():
        if "rexlab argus4" in line:
            # means that we found the line that we want
            parts = line.split()
            if parts:
                print(f"Found board in: {line}")
                print(f"  {parts[0]}")
                return parts[0]  # Return the port (first part of the line)
    return None

def check_folder_board(folder_path):
    """
    Check if the given folder path exists on the board
    """
    
    result = mpremote_run("exec", f"import os; print(not (os.stat('{folder_path}')[0] & 0x4000 == 0))", text=True, capture_output=True, check=False)
    print(f"Checking folder {folder_path} on board: {result.stdout == 'True\\n'}")
    return result.stdout == "True\n"

def check_fs_micro_writable():
    """
    It will check if the micro can write to the file system or if it is in mass storage mode
    will use mpremote exec to try and figure it out
    
    [check] - dont really like the name of this function, need to find something better
    
    return True if writable, False otherwise
    """
    try:
        result = mpremote_run("exec", "import storage; print(storage.getmount('/').readonly)", text=True, capture_output=True, check=False) 
        return result.stdout == "False\n"
    except Exception as e:
        print(f"Got exception {e}")
        return None
            
            
    
PORT = None   # this will be filled at the beggining of the program during the search function
BOARD_PATH = get_board_path()
CPY_VERSION = 9  # Default to CPY 9
if os.path.exists(BOARD_PATH):
    CPY_VERSION = get_circuitpython_version(BOARD_PATH)


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

    # Attempt to remove the SD folder if in CPY 8
    sd_path = os.path.join(destination_folder, "sd")
    if CPY_VERSION == 8 and os.path.exists(sd_path):
        try:
            os.chmod(sd_path, 0o777)
            os.rmdir(sd_path)
            print(f"Removed {sd_path}")
        except PermissionError as e:
            print(f"PermissionError: {e}. Please manually remove the 'sd' folder from the board.")
        except Exception as e:
            print(f"Error: {e}")

    code_py_path = os.path.join(destination_folder, "code.py")
    if os.path.exists(code_py_path):
        try:
            os.chmod(code_py_path, 0o777)
            os.remove(code_py_path)
            print(f"Removed {code_py_path}")
        except PermissionError as e:
            print(f"PermissionError: {e}. Please manually remove the 'code.py' file from the board.")
        except Exception as e:
            print(f"Error: {e}")
            

def mpremote_nuke():
    """
    Simply nukes the board. Erases everything on the board
    after this it will be in state that the micro is not able to write to the file system
    """
    # erase the filesystem
    print("Nuking filesystem...")
    # dont want to check because it will return error because the device will disconnect
    # and will capture the output to avoid spamming the console
    mpremote_run("exec", "import storage; storage.erase_filesystem()", check=False, capture_output=True) 
    
    
def mpremote_changeFs(microWritable=True):
    """
    It will nuke the board, erase everything and make sure that the board is in the desired state
    
    if microWritable is True, after nuking the board it will be able to write to the file system
        after the nuke it will copy the boot.py file to enable the micro writing mode
    if microWritable is False, after nuking the board it will be in mass storage mode
        after nuke it will wait a bit for the board to reconnect
    
    [check] - should add a timeout here
    """

    print("Setting board for micro writing...")
    mpremote_nuke()

    # wait until the board shows back up again
    print("Waiting for board to reconnect...")
    PORT = None
    while PORT is None:
        PORT = search_port()
        time.sleep(0.5)
    time.sleep(2)
    print(f"Board reconnected on port {PORT}")
    
    if not microWritable:
        # if we want mass storage mode, we do not need to do anything else
        print("Board set to mass storage mode.")
        return
    

    # copy the boot.py file to the board (need to copy to the mass storage first)
    print("Copying boot.py to board...")
    dest = "/media/argus/CIRCUITPY/boot.py"
    source = "flight/boot.py"
    
    # check if dest folder exists
    if not os.path.exists(os.path.dirname(dest)):
        print(f"Error: Destination folder '{os.path.dirname(dest)}' does not exist. Is the board connected?")
        exit()
        return
    
    shutil.copy2(source, dest)
    print("boot.py copied.")
    
    # restart the board
    print("Restarting board...")
    mpremote_run("exec", "import microcontroller; microcontroller.reset()", check=False, capture_output=True)
    time.sleep(5)   # wait for the board to boot    
    

def mpremote_copy(source_folder, port):
    """
    Substitute function for copy_folder. But instead of using the mass storage features it will work with mpremote
    chip will be writing to the file system and we will send the info via REPL
    
    for now we will simply copy all the files, but later I will make a system to keep track of the files that have changed
    """
    for root, dirs, files in os.walk(source_folder):

        # device_dir_list = eval(run("exec", "import os; print(os.listdir('/'))", capture_output=True, text=True).stdout)
        
        for d in dirs:
            
            # if d in device_dir_list:
            #     # directory already exists on the board
            #     print(f"Directory {d} already exists on board, skipping creation")
            #     continue
            
            source_dir_path = os.path.join(root, d)
            relative_dir_path = os.path.relpath(source_dir_path, source_folder)
            destination_dir_path = f"/{relative_dir_path}"
            
            if check_folder_board(destination_dir_path):
                # directory already exists on the board
                print(f"Directory {destination_dir_path} already exists on board, skipping creation")
                continue

            # Create directory on the board
            print(f"Creating directory {destination_dir_path} on board")
            mpremote_run("fs", "mkdir", destination_dir_path)

        for file in files:
            source_path = os.path.join(root, file)
            relative_path = os.path.relpath(source_path, source_folder)
            destination_path = f"/{relative_path}"
            dest = os.path.dirname(destination_path)

            # Copy file to the board
            mpremote_run("fs", "cp", "-f", source_path, f":{dest}")
            print(f"Copied {source_path} to {destination_path} on board")
            print(f"   {dest}")
            
    # delete code.py file
    # mpremote rm code.py
    mpremote_run("rm", "code.py", check=False)  # dont care if it fails


if __name__ == "__main__":    
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
    parser.add_argument(
        "-m",
        "--mpremote",
        type=bool,
        default=False,
        help="Use mpremote to copy files instead of mass storage",
        required=False,
    )
    args = parser.parse_args()
    

    source_folder = args.source_folder
    destination_folder = args.destination_folder
    use_mpremote = args.mpremote
    print("Searching for satellite port...")
    PORT = search_port()

    # check if we need to change the file system mode
    microWritable = check_fs_micro_writable()
    if microWritable is None:
        print("Could not determine if the board file system is writable. Is the board connected?")
        exit(1)
    elif microWritable != use_mpremote:
        # need to change the mode
        print(f"Changing file system mode to {'writable' if use_mpremote else 'mass storage'}")
        mpremote_changeFs(microWritable=use_mpremote)

    print("SOURCE FOLDER: ", source_folder)
    if use_mpremote:
        print("USING MPREMOTE")
        mpremote_copy(source_folder, PORT)
    else:
        print("DESTINATION FOLDER: ", destination_folder)

        if not os.path.exists(destination_folder):
            print(f"Error: Destination folder '{destination_folder}' does not exist. Is the board connected?")
            exit(1)
        copy_folder(source_folder, destination_folder, show_identical_files=True)
