import argparse
import filecmp
import os
import shutil


def check_directory_location(source_folder):
    if not os.path.exists(f"{source_folder}"):
        raise FileNotFoundError(f"Source folder {source_folder} not found")


def create_build(source_folder, emulator_folder):
    build_folder = "build/"
    # avoid deleting the whole sd so we can simulate a proper reboot
    if os.path.exists(os.path.join(build_folder, "lib/")):
        shutil.rmtree(os.path.join(build_folder, "lib/"))

    build_folder = os.path.join(build_folder, "lib/")

    os.makedirs(build_folder)

    for root, dirs, files in os.walk(source_folder):
        for file in files:
            # Exclude files in build folder
            if os.path.relpath(root, source_folder).startswith("build/"):
                continue
            if os.path.relpath(root, source_folder).startswith("hal/"):
                continue
            if file.startswith("data_handler"):
                continue
            if file.endswith(".py"):
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

                os.chdir(current_dir)

    # make emulator folder the hal folder
    hal_folder = os.path.join(build_folder, "hal/")
    print(hal_folder)
    for root, dirs, files in os.walk(emulator_folder):
        for file in files:
            source_path = os.path.join(root, file)
            build_path = os.path.join(hal_folder, os.path.relpath(source_path, emulator_folder))
            os.makedirs(os.path.dirname(build_path), exist_ok=True)
            shutil.copy2(source_path, build_path)
            print(f"Copied {source_path} to {build_path}")

    # Adding data_handler.py to the build folder
    # shutil.copy2("flight/core/data_handler.py", "build/lib/core/data_handler.py")
    with open("flight/core/data_handler.py", "r") as file:
        updated_content = file.read().replace('_HOME_PATH = "/sd"', '_HOME_PATH = "sd"')
    with open("build/lib/core/data_handler.py", "w") as file:
        file.write(updated_content)

    # Create main.py file with single import statement "import main_module"
    build_folder = os.path.join(build_folder, "..")
    with open(os.path.join(build_folder, "main.py"), "w") as f:
        f.write("import sys\n")
        f.write("if '/lib' not in sys.path:\n")
        f.write("   sys.path.insert(0, './lib')\n")
        f.write("from hal.accel_time import MockTime\n")
        f.write("sys.modules['time'] = MockTime()\n")
        f.write("import hal.cp_mock\n")
        f.write("import lib.main_module\n")

    # Create SD folder
    os.makedirs(os.path.join(build_folder, "sd/"), exist_ok=True)

    return build_folder


def copy_folder(build_folder, destination_folder, show_identical_files=True):
    for root, dirs, files in os.walk(build_folder):
        for file in files:
            source_path = os.path.join(root, file)
            relative_path = os.path.relpath(source_path, build_folder)
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
            source_path = os.path.join(build_folder, relative_path)

            if not os.path.exists(source_path):
                os.remove(destination_path)
                print(f"Deleted {destination_path}")


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
    parser.add_argument(
        "-e",
        "--emulator_folder",
        type=str,
        default="emulator",
        help="emulator folder path",
        required=False,
    )
    args = parser.parse_args()

    source_folder = args.source_folder
    emulator_folder = args.emulator_folder

    build_folder = create_build(source_folder, emulator_folder)
