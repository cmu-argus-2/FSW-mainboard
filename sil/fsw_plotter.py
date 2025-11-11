import os
import re
import shutil
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np


# Convert timestamp strings to seconds from the start
def timestamps_to_seconds(timestamps):
    dt_format = "%Y-%m-%d %H:%M:%S"
    dt_objs = [datetime.strptime(ts, dt_format) for ts in timestamps]
    start_time = dt_objs[0]
    return np.array([(dt - start_time).total_seconds() for dt in dt_objs])


def undersample(data, percentage):
    if not 0 < percentage <= 100:
        raise ValueError("Percentage must be between 0 and 100")
    step = max(1, int(100 / percentage))
    return data[::step]


def plot_FSW(result_folder_path):
    """
    Plots the FSW data.
    """
    plots_folder_path = os.path.join(result_folder_path, "plots")
    # trials folder path
    trials_folder_path = os.path.join(result_folder_path, "trials")
    # Collect list of trial folders
    trial_folders = [
        os.path.join(trials_folder_path, d)
        for d in os.listdir(trials_folder_path)
        if os.path.isdir(os.path.join(trials_folder_path, d))
    ]
    adcs_modes_list = []
    global_modes_list = []
    gyro_ang_vels_list = []
    mag_fields_list = []
    sun_vectors_list = []
    sun_statuses_list = []
    trial_numbers = []
    for i, trial_folder in enumerate(trial_folders):
        # load FSW data for each trial
        data_path = os.path.join(trial_folder, "fsw_extracted_data.npz")
        if not os.path.exists(data_path):
            print(f"Extracted data file not found at {data_path}")
            return
        # Extract trial number from the folder name (assumes folder ends with an integer)
        trial_number_match = re.search(r"(\d+)$", trial_folder)
        if trial_number_match:
            trial_number = int(trial_number_match.group(1))
        else:
            trial_number = None
        trial_numbers.append(trial_number)
        data = np.load(data_path, allow_pickle=True)

        # Extract arrays by key
        adcs_modes = data["adcs_modes"]
        global_modes = data["global_modes"]
        gyro_ang_vels = data["gyro_ang_vels"]

        # Extract timestamps from the first column of each array
        timestamps_modes = adcs_modes[:, 0]
        timestamps_global = global_modes[:, 0]
        timestamps_gyro = gyro_ang_vels[:, 0]

        # Convert data columns to appropriate types
        adcs_modes_values = adcs_modes[:, 1].astype(int)
        global_modes_values = global_modes[:, 1].astype(int)
        gyro_ang_vel = gyro_ang_vels[:, 1:4].astype(float)

        timestamps_gyro = timestamps_to_seconds(timestamps_gyro)
        timestamps_modes = timestamps_to_seconds(timestamps_modes)
        timestamps_global = timestamps_to_seconds(timestamps_global)

        mag_fields = data["mag_fields"]
        timestamps_mag = timestamps_to_seconds(mag_fields[:, 0])
        mag_field = mag_fields[:, 1:4].astype(float)

        sun_vectors = data["sun_vectors"]
        timestamps_sun = timestamps_to_seconds(sun_vectors[:, 0])
        sun_vector = sun_vectors[:, 1:4].astype(float)

        sun_statuses = data["sun_statuses"]
        timestamps_status = timestamps_to_seconds(sun_statuses[:, 0])
        sun_status = sun_statuses[:, 1].astype(int)

        # Store everything into lists
        adcs_modes_list.append((timestamps_modes, adcs_modes_values))
        global_modes_list.append((timestamps_global, global_modes_values))
        gyro_ang_vels_list.append((timestamps_gyro, gyro_ang_vel))
        mag_fields_list.append((timestamps_mag, mag_field))
        sun_vectors_list.append((timestamps_sun, sun_vector))
        sun_statuses_list.append((timestamps_status, sun_status))

    print("Plotting FSW data...")
    # Use timestamps_gyro for plotting (assuming all timestamps are aligned)
    # Plot ADCS Mode
    # Plot ADCS Mode
    mode_names = ["TUMBLING", "STABLE", "SUN_POINTED", "ACS_OFF"]
    global_mode_names = ["STARTUP", "DETUMBLING", "NOMINAL", "EXPERIMENT", "LOW_POWER"]

    plt.figure(figsize=(12, 7))

    # ADCS Mode subplot
    ax1 = plt.subplot(2, 1, 1)
    for trial_idx, (timestamps_modes, adcs_modes_values) in enumerate(adcs_modes_list):
        ax1.plot(timestamps_modes, adcs_modes_values, label=f"Trial {trial_numbers[trial_idx]}")
    ax1.set_ylabel("ADCS Mode")
    ax1.set_yticks(range(len(mode_names)))
    ax1.set_yticklabels(mode_names)
    ax1.legend()
    ax1.set_title("ADCS Mode")

    # Global Mode subplot
    ax2 = plt.subplot(2, 1, 2, sharex=ax1)
    for trial_idx, (timestamps_global, global_modes_values) in enumerate(global_modes_list):
        ax2.plot(timestamps_global, global_modes_values, label=f"Trial {trial_numbers[trial_idx]}")
    ax2.set_ylabel("Global Mode")
    ax2.set_xlabel("Time (s)")
    ax2.set_yticks(range(len(global_mode_names)))
    ax2.set_yticklabels(global_mode_names)
    ax2.legend()
    ax2.set_title("Global Mode")

    plt.tight_layout()
    output_plot_path_modes = os.path.join(plots_folder_path, "fsw_modes_subplot.png")
    plt.savefig(output_plot_path_modes)
    plt.close()
    print(f"ADCS and Global Mode subplot saved to {output_plot_path_modes}")

    # Plot Gyro Angular Velocity
    plt.figure(figsize=(10, 8))
    axes = []
    labels = ["Gyro X [deg/s]", "Gyro Y [deg/s]", "Gyro Z [deg/s]"]
    for i in range(3):
        ax = plt.subplot(3, 1, i + 1)
        for trial_idx, (timestamps_gyro, gyro_ang_vel) in enumerate(gyro_ang_vels_list):
            ax.plot(timestamps_gyro, np.rad2deg(gyro_ang_vel[:, i]), label=f"Trial {trial_numbers[trial_idx]}")
        ax.set_ylabel(labels[i])
        if i == 2:
            ax.set_xlabel("Time (s)")
        if i == 0:
            ax.legend()
        ax.set_title("ADCS Angular Velocity")
        axes.append(ax)
    plt.tight_layout()
    output_plot_path_gyro = os.path.join(plots_folder_path, "fsw_gyro_ang_vel_plot.png")
    plt.savefig(output_plot_path_gyro)
    plt.close()
    print(f"Gyro Angular Velocity plot saved to {output_plot_path_gyro}")

    # Plot Magnetic Field
    plt.figure(figsize=(10, 8))
    labels = ["Mag X [T]", "Mag Y [T]", "Mag Z [T]"]
    for i in range(3):
        ax = plt.subplot(3, 1, i + 1)
        for trial_idx, (timestamps_mag, mag_field) in enumerate(mag_fields_list):
            ax.plot(timestamps_mag, mag_field[:, i], label=f"Trial {trial_numbers[trial_idx]}")
        ax.set_ylabel(labels[i])
        if i == 2:
            ax.set_xlabel("Time (s)")
        if i == 0:
            ax.legend()
            ax.set_title("ADCS Magnetic Field")
    plt.tight_layout()
    output_plot_path_mag = os.path.join(plots_folder_path, "fsw_mag_field_plot.png")
    plt.savefig(output_plot_path_mag)
    plt.close()
    print(f"Mag Field plot saved to {output_plot_path_mag}")

    # Plot Sun Vector
    plt.figure(figsize=(10, 8))
    labels = ["Sun X", "Sun Y", "Sun Z"]
    for i in range(3):
        ax = plt.subplot(3, 1, i + 1)
        for trial_idx, (timestamps_sun, sun_vector) in enumerate(sun_vectors_list):
            ax.plot(timestamps_sun, sun_vector[:, i], label=f"Trial {trial_numbers[trial_idx]}")
        ax.set_ylabel(labels[i])
        if i == 2:
            ax.set_xlabel("Time (s)")
        if i == 0:
            ax.legend()
            ax.set_title("ADCS Sun Vector")
    plt.tight_layout()
    output_plot_path_sun = os.path.join(plots_folder_path, "fsw_sun_vector_plot.png")
    plt.savefig(output_plot_path_sun)
    plt.close()
    print(f"Sun Vector plot saved to {output_plot_path_sun}")

    # Plot Sun Status
    sun_mode_names = ["SUN_FLAG_ZERO", "SUN_NO_READINGS", "SUN_NOT_ENOUGH_READINGS", "SUN_ECLIPSE"]
    plt.figure(figsize=(10, 4))
    for trial_idx, (timestamps_status, sun_status) in enumerate(sun_statuses_list):
        # Set all sun_status == 0 to 50 for plotting
        sun_status_plot = np.where(sun_status == 0, 50, sun_status)
        plt.plot(timestamps_status, sun_status_plot, label=f"Trial {trial_numbers[trial_idx]}")
    plt.ylabel("Sun Status")
    plt.xlabel("Time (s)")
    plt.yticks(ticks=range(50, 50 + len(sun_mode_names)), labels=sun_mode_names)
    plt.ylim(49, 54)
    plt.legend()
    plt.title("ADCS Sun Status")
    plt.tight_layout()
    output_plot_path_status = os.path.join(plots_folder_path, "fsw_sun_status_plot.png")
    plt.savefig(output_plot_path_status)
    plt.close()
    print(f"Sun Status plot saved to {output_plot_path_status}")


def collect_FSW_data(outfile, result_folder_path, save_sil_logs=False, erase_sil_logs=False, percent_to_log=1):
    """
    Collects FSW data from the log file.
    """
    print(f"Collecting FSW data from {outfile}...")
    fsw_data = []
    pattern = re.compile(r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]\[INFO\] \[\d+\]\[ADCS\] .+:.+")
    command_global_state_pattern = re.compile(
        r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]\[INFO\] \[\d+\]\[COMMAND\] GLOBAL STATE: .+"
    )
    with open(outfile, "r") as f:
        for line in f:
            if pattern.match(line.strip()) or command_global_state_pattern.match(line.strip()):
                fsw_data.append(line.strip())

    print(f"Collected {len(fsw_data)} FSW data entries.")
    # Extract timestamp, ADCS Mode, Gyro Ang Vel, and Gyro Bias
    # Prepare empty lists for each variable
    # [2024-10-21 09:20:32][INFO] [0][COMMAND] GLOBAL STATE: DETUMBLING.
    # Also append to fsw_data the command global state pattern
    adcs_modes = []
    global_modes = []
    gyro_ang_vels = []
    mag_fields = []
    sun_vectors = []
    sun_statuses = []

    for entry in fsw_data:
        timestamp = entry.split("]")[0][1:]
        adcs_mode = re.search(r"ADCS Mode : (\d+)", entry)
        global_mode = re.search(r"GLOBAL STATE: (\w+)", entry)
        gyro_ang_vel = re.search(r"Gyro Ang Vel : \[(.*?)\]", entry)
        mag_field = re.search(r"Mag Field : \[(.*?)\]", entry)
        sun_vector = re.search(r"Sun Vector : \[(.*?)\]", entry)
        sun_status = re.search(r"Sun Status : (\d+)", entry)
        global_mode_code = {
            "STARTUP": 0,
            "DETUMBLING": 1,
            "NOMINAL": 2,
            "EXPERIMENT": 3,
            "LOW_POWER": 4,
        }

        if adcs_mode:
            adcs_modes.append([timestamp, int(adcs_mode.group(1))])
        elif global_mode:
            global_modes.append([timestamp, global_mode_code[global_mode.group(1)]])
        elif gyro_ang_vel:
            values = re.findall(r"np\.float64\((.*?)\)", gyro_ang_vel.group(1))
            if not values:
                values = re.findall(r"[-+]?\d*\.\d+(?:[eE][-+]?\d+)?|[-+]?\d+(?:[eE][-+]?\d+)?", gyro_ang_vel.group(1))
            gyro_ang_vels.append([timestamp] + [float(v) for v in values])
        elif mag_field:
            values = re.findall(r"[-+]?\d*\.\d+(?:[eE][-+]?\d+)?|[-+]?\d+(?:[eE][-+]?\d+)?", mag_field.group(1))
            mag_fields.append([timestamp] + [float(v) for v in values])
        elif sun_vector:
            values = re.findall(r"[-+]?\d*\.\d+(?:[eE][-+]?\d+)?|[-+]?\d+(?:[eE][-+]?\d+)?", sun_vector.group(1))
            sun_vectors.append([timestamp] + [float(v) for v in values])
        elif sun_status:
            sun_statuses.append([timestamp, int(sun_status.group(1))])

    # Convert lists to numpy arrays (timestamps already included)
    adcs_modes_np = np.array(adcs_modes)
    global_modes_np = np.array(global_modes)
    gyro_ang_vels_np = np.array(gyro_ang_vels)
    mag_fields_np = np.array(mag_fields)
    sun_vectors_np = np.array(sun_vectors)
    sun_statuses_np = np.array(sun_statuses)

    # Undersample the data to a given percentage
    adcs_modes_np = undersample(adcs_modes_np, 100 * percent_to_log)
    global_modes_np = undersample(global_modes_np, 100 * percent_to_log)
    gyro_ang_vels_np = undersample(gyro_ang_vels_np, 100 * percent_to_log)
    mag_fields_np = undersample(mag_fields_np, 100 * percent_to_log)
    sun_vectors_np = undersample(sun_vectors_np, 100 * percent_to_log)
    sun_statuses_np = undersample(sun_statuses_np, 100 * percent_to_log)

    # Save extracted data to a .npz file in the result folder
    if not os.path.exists(result_folder_path):
        os.makedirs(result_folder_path)
    output_path = os.path.join(result_folder_path, "fsw_extracted_data.npz")
    np.savez(
        output_path,
        adcs_modes=adcs_modes_np,
        global_modes=global_modes_np,
        gyro_ang_vels=gyro_ang_vels_np,
        mag_fields=mag_fields_np,
        sun_vectors=sun_vectors_np,
        sun_statuses=sun_statuses_np,
    )
    print(f"Extracted data saved to {output_path}")

    # Move sil_logs.log to the result folder
    if save_sil_logs:
        shutil.copy(outfile, result_folder_path)
    if erase_sil_logs:
        os.remove(outfile)
