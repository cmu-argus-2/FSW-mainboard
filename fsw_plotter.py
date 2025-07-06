import re
import numpy as np
import os
from datetime import datetime
import shutil
import matplotlib.pyplot as plt

# Convert timestamp strings to seconds from the start
def timestamps_to_seconds(timestamps):
    dt_format = "%Y-%m-%d %H:%M:%S"
    dt_objs = [datetime.strptime(ts, dt_format) for ts in timestamps]
    start_time = dt_objs[0]
    return np.array([(dt - start_time).total_seconds() for dt in dt_objs])


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
    gyro_ang_vels_list = []
    gyro_biases_list = []
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
        trial_number_match = re.search(r'(\d+)$', trial_folder)
        if trial_number_match:
            trial_number = int(trial_number_match.group(1))
        else:
            trial_number = None
        trial_numbers.append(trial_number)
        data = np.load(data_path, allow_pickle=True)

        # Extract arrays by key
        adcs_modes = data["adcs_modes"]
        gyro_ang_vels = data["gyro_ang_vels"]
        gyro_biases = data["gyro_biases"]

        # Extract timestamps from the first column of each array
        timestamps_modes = adcs_modes[:, 0]
        timestamps_gyro = gyro_ang_vels[:, 0]
        timestamps_bias = gyro_biases[:, 0]

        # Convert data columns to appropriate types
        adcs_modes_values = adcs_modes[:, 1].astype(int)
        gyro_ang_vel = gyro_ang_vels[:, 1:4].astype(float)
        gyro_bias = gyro_biases[:, 1:4].astype(float)

        timestamps_gyro = timestamps_to_seconds(timestamps_gyro)
        timestamps_modes = timestamps_to_seconds(timestamps_modes)
        timestamps_bias = timestamps_to_seconds(timestamps_bias)

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
        gyro_ang_vels_list.append((timestamps_gyro, gyro_ang_vel))
        gyro_biases_list.append((timestamps_bias, gyro_bias))
        mag_fields_list.append((timestamps_mag, mag_field))
        sun_vectors_list.append((timestamps_sun, sun_vector))
        sun_statuses_list.append((timestamps_status, sun_status))

        

    print("Plotting FSW data...")
    # Use timestamps_gyro for plotting (assuming all timestamps are aligned)
    # Plot ADCS Mode
    mode_names = ["TUMBLING", "STABLE", "SUN_POINTED", "ACS_OFF"]
    plt.figure(figsize=(10, 4))
    for idx, (timestamps_modes, adcs_modes_values) in enumerate(adcs_modes_list):
        plt.plot(timestamps_modes, adcs_modes_values, label=f"Trial {idx+1}")
    plt.ylabel("ADCS Mode")
    plt.xlabel("Time (s)")
    plt.yticks(ticks=range(len(mode_names)), labels=mode_names)
    plt.legend()
    plt.tight_layout()
    plt.title("ADCS Mode")
    output_plot_path_mode = os.path.join(plots_folder_path, "fsw_adcs_mode_plot.png")
    plt.savefig(output_plot_path_mode)
    plt.close()
    print(f"ADCS Mode plot saved to {output_plot_path_mode}")

    # Plot Gyro Angular Velocity
    plt.figure(figsize=(10, 8))
    axes = []
    labels = ["Gyro X [deg/s]", "Gyro Y [deg/s]", "Gyro Z [deg/s]"]
    for i in range(3):
        ax = plt.subplot(3, 1, i + 1)
        for trial_idx, (timestamps_gyro, gyro_ang_vel) in enumerate(gyro_ang_vels_list):
            ax.plot(timestamps_gyro, gyro_ang_vel[:, i], label=f"Trial {trial_numbers[trial_idx]}")
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

    # Plot Gyro Bias
    plt.figure(figsize=(10, 8))
    labels = ["Bias X", "Bias Y", "Bias Z"]
    for i in range(3):
        ax = plt.subplot(3, 1, i + 1)
        for trial_idx, (timestamps_bias, gyro_bias) in enumerate(gyro_biases_list):
            ax.plot(timestamps_bias, gyro_bias[:, i], label=f"Trial {trial_numbers[trial_idx]}")
        ax.set_ylabel(labels[i])
        if i == 2:
            ax.set_xlabel("Time (s)")
        if i == 0:
            ax.legend()
            ax.set_title("ADCS Gyro Bias")

    plt.tight_layout()
    output_plot_path_bias = os.path.join(plots_folder_path, "fsw_gyro_bias_plot.png")
    plt.savefig(output_plot_path_bias)
    plt.close()
    print(f"Gyro Bias plot saved to {output_plot_path_bias}")

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
    colors = ['tab:blue', 'tab:orange', 'tab:green']
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
    # [TODO:] set y labels to the corresponding codes
    plt.figure(figsize=(10, 4))
    for trial_idx, (timestamps_status, sun_status) in enumerate(sun_statuses_list):
        plt.plot(timestamps_status, sun_status, label=f"Trial {trial_numbers[trial_idx]}")
    plt.ylabel("Sun Status")
    plt.xlabel("Time (s)")
    plt.legend()
    plt.title("ADCS Sun Status")
    plt.tight_layout()
    output_plot_path_status = os.path.join(plots_folder_path, "fsw_sun_status_plot.png")
    plt.savefig(output_plot_path_status)
    plt.close()
    print(f"Sun Status plot saved to {output_plot_path_status}")
        


def collect_FSW_data(outfile, result_folder_path):
    """
    Collects FSW data from the log file.
    """
    print(f"Collecting FSW data from {outfile}...")
    fsw_data = []
    pattern = re.compile(r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]\[INFO\] \[\d+\]\[ADCS\] .+:.+")

    with open(outfile, 'r') as f:
        for line in f:
            if pattern.match(line.strip()):
                fsw_data.append(line.strip())

    print(f"Collected {len(fsw_data)} FSW data entries.")
    # [2024-10-01 21:21:26][INFO] [6][ADCS] ADCS Mode : 1
    # [2024-10-01 21:21:26][INFO] [6][ADCS] Gyro Ang Vel : [np.float64(0.0), np.float64(0.0), np.float64(0.0)]
    # [2024-10-01 21:21:26][INFO] [6][ADCS] Gyro Bias : [0. 0. 0.]
    # [2024-10-27 23:16:05][INFO] [6][ADCS] Mag Field : [-3.477101329337895e-05, -2.7282350701214218e-05, 1.3561380237317155e-05]
    # [2024-10-27 23:16:05][INFO] [6][ADCS] Sun Vector : [-0.18666812846588665, -0.862232934081153, -0.4708602523051283]
    # [2024-10-27 23:16:05][INFO] [6][ADCS] Sun Status : 0
    # Extract timestamp, ADCS Mode, Gyro Ang Vel, and Gyro Bias
    # Prepare empty lists for each variable
    adcs_modes = []
    gyro_ang_vels = []
    gyro_biases = []
    mag_fields = []
    sun_vectors = []
    sun_statuses = []

    for entry in fsw_data:
        timestamp = entry.split(']')[0][1:]
        adcs_mode = re.search(r'ADCS Mode : (\d+)', entry)
        gyro_ang_vel = re.search(r'Gyro Ang Vel : \[(.*?)\]', entry)
        gyro_bias = re.search(r'Gyro Bias : \[(.+?)\]', entry)
        mag_field = re.search(r'Mag Field : \[(.*?)\]', entry)
        sun_vector = re.search(r'Sun Vector : \[(.*?)\]', entry)
        sun_status = re.search(r'Sun Status : (\d+)', entry)

        if adcs_mode:
            adcs_modes.append([timestamp, int(adcs_mode.group(1))])
        elif gyro_ang_vel:
            values = re.findall(r'np\.float64\((.*?)\)', gyro_ang_vel.group(1))
            if not values:
                values = re.findall(r'[-+]?\d*\.\d+(?:[eE][-+]?\d+)?|[-+]?\d+(?:[eE][-+]?\d+)?', gyro_ang_vel.group(1))
            gyro_ang_vels.append([timestamp] + [float(v) for v in values])
        elif gyro_bias:
            values = re.findall(r'[-+]?\d*\.\d+(?:[eE][-+]?\d+)?|[-+]?\d+(?:[eE][-+]?\d+)?', gyro_bias.group(1))
            gyro_biases.append([timestamp] + [float(v) for v in values])
        elif mag_field:
            values = re.findall(r'[-+]?\d*\.\d+(?:[eE][-+]?\d+)?|[-+]?\d+(?:[eE][-+]?\d+)?', mag_field.group(1))
            mag_fields.append([timestamp] + [float(v) for v in values])
        elif sun_vector:
            values = re.findall(r'[-+]?\d*\.\d+(?:[eE][-+]?\d+)?|[-+]?\d+(?:[eE][-+]?\d+)?', sun_vector.group(1))
            sun_vectors.append([timestamp] + [float(v) for v in values])
        elif sun_status:
            sun_statuses.append([timestamp, int(sun_status.group(1))])

    # Convert lists to numpy arrays (timestamps already included)
    adcs_modes_np = np.array(adcs_modes)
    gyro_ang_vels_np = np.array(gyro_ang_vels)
    gyro_biases_np = np.array(gyro_biases)
    mag_fields_np = np.array(mag_fields)
    sun_vectors_np = np.array(sun_vectors)
    sun_statuses_np = np.array(sun_statuses)
    
    # Save extracted data to a .npz file in the result folder
    output_path = os.path.join(result_folder_path, "fsw_extracted_data.npz")
    np.savez(output_path, 
             adcs_modes=adcs_modes_np, 
             gyro_ang_vels=gyro_ang_vels_np, 
             gyro_biases=gyro_biases_np,
             mag_fields=mag_fields_np,
             sun_vectors=sun_vectors_np,
             sun_statuses=sun_statuses_np)
    print(f"Extracted data saved to {output_path}")

    # Move sil_logs.log to the result folder
    shutil.move(outfile, result_folder_path)
    