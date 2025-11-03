import argparse
import os
import shutil

try:
    import yaml

    _HAS_YAML = True
except Exception:
    yaml = None
    _HAS_YAML = False


def generate_satellite_config(source_folder, use_flight_config=False):
    """
    Generate satellite_config.py from ground.yaml or flight.yaml.

    Args:
        source_folder: Path to the flight source folder
        use_flight_config: If True, use flight.yaml; otherwise use ground.yaml
    """
    if not _HAS_YAML:
        raise ImportError("PyYAML is not installed; cannot generate satellite_config.py")

    config_file = "flight.yaml" if use_flight_config else "ground.yaml"
    yaml_path = os.path.join(source_folder, "configuration", config_file)

    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"Configuration file {yaml_path} not found; cannot generate satellite_config.py")

    try:
        with open(yaml_path, "r") as yf:
            config_data = yaml.safe_load(yf)

        if config_data is None:
            print(f"Configuration file {yaml_path} is empty; skipping generation of satellite_config.py")
            return

        output_lines = [
            "# Auto-generated from " + config_file,
            "# Do not edit - changes will be overwritten by the build system.",
            "",
            "from micropython import const",
            "",
        ]

        for category_name, category_data in config_data.items():
            if category_data is None:
                continue

            class_name = category_name + "_config"
            output_lines.append(f"class {class_name}:")

            if not category_data or not isinstance(category_data, dict):
                output_lines.append("    pass")
                output_lines.append("")
                continue

            for key, value in category_data.items():
                if isinstance(value, dict) and "value" in value:
                    actual_value = value["value"]
                    use_const = value.get("_const", False)

                    if use_const and isinstance(actual_value, int):
                        python_value = f"const({actual_value})"
                    elif isinstance(actual_value, str):
                        python_value = repr(actual_value)
                    elif isinstance(actual_value, (int, float, bool)):
                        python_value = repr(actual_value)
                    elif isinstance(actual_value, list):
                        python_value = repr(actual_value)
                    elif isinstance(actual_value, dict):
                        python_value = repr(actual_value)
                    else:
                        python_value = repr(actual_value)
                else:
                    # Simple value without metadata, if no const defined
                    if isinstance(value, str):
                        python_value = repr(value)
                    elif isinstance(value, (int, float, bool)):
                        python_value = repr(value)
                    elif isinstance(value, list):
                        python_value = repr(value)
                    elif isinstance(value, dict):
                        python_value = repr(value)
                    else:
                        python_value = repr(value)

                output_lines.append(f"    {key} = {python_value}")

            output_lines.append("")

        core_folder = os.path.join(source_folder, "core")
        if not os.path.exists(core_folder):
            os.makedirs(core_folder, exist_ok=True)

        config_py_path = os.path.join(core_folder, "satellite_config.py")
        with open(config_py_path, "w") as py_file:
            py_file.write("\n".join(output_lines))

        print(f"Generated {config_py_path} from {config_file}")

    except Exception as e:
        print(f"Failed to generate satellite_config.py from {yaml_path}: {e}")


def get_commit_hash():
    try:
        commit_hash = os.popen("git rev-parse --short HEAD").read().strip()
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
        f.write("import hal.cp_mock\n")
        f.write("import lib.main_module\n")

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
    parser.add_argument(
        "-e",
        "--emulator_folder",
        type=str,
        default="emulator",
        help="emulator folder path",
        required=False,
    )
    parser.add_argument(
        "--flight",
        action="store_true",
        help="Use flight.yaml configuration instead of ground.yaml",
    )
    args = parser.parse_args()

    source_folder = args.source_folder
    emulator_folder = args.emulator_folder

    generate_satellite_config(source_folder, use_flight_config=args.flight)

    GIT_BRANCH = get_branch_name()
    GIT_COMMIT = get_commit_hash()
    if GIT_BRANCH:
        print(f"Branch: {GIT_BRANCH}")
    if GIT_COMMIT:
        print(f"Commit: {GIT_COMMIT}")

    build_folder = create_build(source_folder, emulator_folder)
