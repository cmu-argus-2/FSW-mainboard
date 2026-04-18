import os
import re
import shutil
import sys
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np

# flake8: noqa: E402
project_root = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.abspath(os.path.join(project_root, ".."))

# Add the project root to PYTHONPATH if it isn't already
if project_root not in sys.path:
    sys.path.append(project_root)


def _parse_measurements_bin(filepath):
    """Parse a measurements.bin file into a dict of {column_label: np.ndarray}."""
    import struct

    file_size = os.path.getsize(filepath)
    with open(filepath, "rb") as f:
        header = f.readline().decode("utf-8").strip().strip(",")
        columns = header.split(",")
        n_cols = len(columns)
        n_data_bytes = file_size - f.tell()
        n_rows = n_data_bytes // (8 * n_cols)
        raw = f.read(n_rows * n_cols * 8)
    data = np.array(struct.unpack(f"{n_rows * n_cols}d", raw)).reshape(n_rows, n_cols)
    return {col: data[:, i] for i, col in enumerate(columns)}


def undersample(data, percentage):
    if not 0 < percentage <= 100:
        raise ValueError("Percentage must be between 0 and 100")
    step = max(1, int(100 / percentage))
    return data[::step]


def plot_FSW(result_folder_path, plot_sim_mag=True):
    """
    Plots the FSW data from SIL campaigns (multi-trial).
    plot_sim_mag: if True, overlay the simulation ground-truth magnetic field from measurements.bin.
    """
    plots_folder_path = os.path.join(result_folder_path, "plots")
    trials_folder_path = os.path.join(result_folder_path, "trials")
    trial_folders = [
        os.path.join(trials_folder_path, d)
        for d in os.listdir(trials_folder_path)
        if os.path.isdir(os.path.join(trials_folder_path, d))
    ]
    adcs_modes_list = []
    global_modes_list = []
    gyro_ang_vels_list = []
    mag_fields_list = []
    sim_mag_list = []
    sim_gyro_list = []
    sun_vectors_list = []
    sun_statuses_list = []
    trial_numbers = []
    for i, trial_folder in enumerate(trial_folders):
        data_path = os.path.join(trial_folder, "fsw_extracted_data.npz")
        if not os.path.exists(data_path):
            print(f"Extracted data file not found at {data_path}")
            return
        trial_number_match = re.search(r"(\d+)$", trial_folder)
        trial_number = int(trial_number_match.group(1)) if trial_number_match else None
        trial_numbers.append(trial_number)
        data = np.load(data_path, allow_pickle=True)

        adcs_modes = data["adcs_modes"]
        global_modes = data["global_modes"]
        gyro_ang_vels = data["gyro_ang_vels"]

        timestamps_modes = adcs_modes[:, 0].astype(float)
        timestamps_global = global_modes[:, 0].astype(float)
        timestamps_gyro = gyro_ang_vels[:, 0].astype(float)

        adcs_modes_values = adcs_modes[:, 1].astype(int)
        global_modes_values = global_modes[:, 1].astype(int)
        gyro_ang_vel = gyro_ang_vels[:, 1:4].astype(float)

        mag_fields = data["mag_fields"]
        timestamps_mag = mag_fields[:, 0].astype(float)
        mag_field = mag_fields[:, 1:4].astype(float)

        sun_vectors = data["sun_vectors"]
        timestamps_sun = sun_vectors[:, 0].astype(float)
        sun_vector = sun_vectors[:, 1:4].astype(float)

        sun_statuses = data["sun_statuses"]
        timestamps_status = sun_statuses[:, 0].astype(float)
        sun_status = sun_statuses[:, 1].astype(int)

        sim_mag = None
        sim_gyro = None
        measurements_path = os.path.join(trial_folder, "measurements.bin")
        if plot_sim_mag and os.path.exists(measurements_path):
            meas = _parse_measurements_bin(measurements_path)
            sim_t = meas["Time [s]"]
            sim_mag = (
                sim_t,
                np.column_stack([meas["mag_x_body [muT]"], meas["mag_y_body [muT]"], meas["mag_z_body [muT]"]]),
            )
            sim_gyro = (
                sim_t,
                np.column_stack([meas["gyro_x [deg/s]"], meas["gyro_y [deg/s]"], meas["gyro_z [deg/s]"]]),
            )

        adcs_modes_list.append((timestamps_modes, adcs_modes_values))
        global_modes_list.append((timestamps_global, global_modes_values))
        gyro_ang_vels_list.append((timestamps_gyro, gyro_ang_vel))
        mag_fields_list.append((timestamps_mag, mag_field))
        sim_mag_list.append(sim_mag)
        sim_gyro_list.append(sim_gyro)
        sun_vectors_list.append((timestamps_sun, sun_vector))
        sun_statuses_list.append((timestamps_status, sun_status))

    adcs_times = (
        [t for ts, _ in adcs_modes_list for t in ts]
        + [t for ts, _ in gyro_ang_vels_list for t in ts]
        + [t for ts, _ in mag_fields_list for t in ts]
        + [t for ts, _ in sun_vectors_list for t in ts]
        + [t for ts, _ in sun_statuses_list for t in ts]
    )
    fsw_xlim_adcs = (min(adcs_times), max(adcs_times))
    all_fsw_times = adcs_times + [t for ts, _ in global_modes_list for t in ts]
    fsw_xlim_all = (min(all_fsw_times), max(all_fsw_times))

    print("Plotting FSW data...")
    mode_names = ["TUMBLING", "STABLE", "SUN_POINTED", "ACS_OFF"]
    global_mode_names = ["STARTUP", "DETUMBLING", "NOMINAL", "EXPERIMENT", "LOW_POWER"]

    plt.figure(figsize=(12, 7))
    ax1 = plt.subplot(2, 1, 1)
    for trial_idx, (timestamps_modes, adcs_modes_values) in enumerate(adcs_modes_list):
        ax1.plot(timestamps_modes, adcs_modes_values, label=f"Trial {trial_numbers[trial_idx]}", marker=".", drawstyle="steps-post")
    ax1.set_xlim(fsw_xlim_all)
    ax1.set_ylabel("ADCS Mode")
    ax1.set_yticks(range(len(mode_names)))
    ax1.set_yticklabels(mode_names)
    ax1.legend()
    ax1.set_title("ADCS Mode")

    ax2 = plt.subplot(2, 1, 2, sharex=ax1)
    for trial_idx, (timestamps_global, global_modes_values) in enumerate(global_modes_list):
        ax2.plot(timestamps_global, global_modes_values, label=f"Trial {trial_numbers[trial_idx]}", marker=".", drawstyle="steps-post")
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

    plt.figure(figsize=(10, 8))
    axes = []
    labels = ["Gyro X [deg/s]", "Gyro Y [deg/s]", "Gyro Z [deg/s]"]
    for i in range(3):
        ax = plt.subplot(3, 1, i + 1)
        for trial_idx, (timestamps_gyro, gyro_ang_vel) in enumerate(gyro_ang_vels_list):
            color = f"C{trial_idx}"
            ax.plot(timestamps_gyro, np.rad2deg(gyro_ang_vel[:, i]), label=f"Trial {trial_numbers[trial_idx]} FSW", marker=".", drawstyle="steps-post", color=color)
            if sim_gyro_list[trial_idx] is not None:
                sim_t, sim_gyro = sim_gyro_list[trial_idx]
                ax.plot(sim_t, sim_gyro[:, i], label=f"Trial {trial_numbers[trial_idx]} sim", linestyle="--", linewidth=0.8, color=color)
        ax.set_xlim(fsw_xlim_adcs)
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

    plt.figure(figsize=(10, 8))
    labels = ["Mag X [uT]", "Mag Y [uT]", "Mag Z [uT]"]
    for i in range(3):
        ax = plt.subplot(3, 1, i + 1)
        for trial_idx, (timestamps_mag, mag_field) in enumerate(mag_fields_list):
            color = f"C{trial_idx}"
            ax.plot(timestamps_mag, 1e6 * mag_field[:, i], label=f"Trial {trial_numbers[trial_idx]} FSW", marker=".", drawstyle="steps-post", color=color)
            if sim_mag_list[trial_idx] is not None:
                sim_t, sim_mag = sim_mag_list[trial_idx]
                ax.plot(sim_t, sim_mag[:, i], label=f"Trial {trial_numbers[trial_idx]} sim", linestyle="--", linewidth=0.8, color=color)
        ax.set_xlim(fsw_xlim_adcs)
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

    plt.figure(figsize=(10, 8))
    labels = ["Sun X", "Sun Y", "Sun Z"]
    for i in range(3):
        ax = plt.subplot(3, 1, i + 1)
        for trial_idx, (timestamps_sun, sun_vector) in enumerate(sun_vectors_list):
            ax.plot(timestamps_sun, sun_vector[:, i], label=f"Trial {trial_numbers[trial_idx]}", marker=".", drawstyle="steps-post")
        ax.set_xlim(fsw_xlim_adcs)
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

    sun_mode_names = ["SUN_FLAG_ZERO", "SUN_NO_READINGS", "SUN_NOT_ENOUGH_READINGS", "SUN_ECLIPSE"]
    plt.figure(figsize=(10, 4))
    for trial_idx, (timestamps_status, sun_status) in enumerate(sun_statuses_list):
        sun_status_plot = np.where(sun_status == 0, 50, sun_status)
        plt.plot(timestamps_status, sun_status_plot, label=f"Trial {trial_numbers[trial_idx]}", marker=".", drawstyle="steps-post")
    plt.xlim(fsw_xlim_adcs)
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
    All timestamps are stored as seconds since the first timestamped line in the log,
    derived from wall-clock time. This correctly handles ADCS time resets across reboots.
    """
    print(f"Collecting FSW data from {outfile}...")

    dt_format = "%Y-%m-%d %H:%M:%S"
    first_wall_time = None
    current_wall_t = 0.0

    global_mode_code = {"STARTUP": 0, "DETUMBLING": 1, "NOMINAL": 2, "EXPERIMENT": 3, "LOW_POWER": 4}
    payload_state_code = {"OFF": 0, "POWERING_ON": 1, "READY": 2, "SHUTTING_DOWN": 3}
    coil_axes = ["XP", "XM", "YP", "YM", "ZP", "ZM"]

    # Data lists
    adcs_modes = []
    controller_modes = []
    global_modes = []
    gyro_ang_vels = []
    mag_fields = []
    sun_vectors = []
    sun_statuses = []
    cpu_temps = []
    ram_usages = []
    payload_states = []
    eps_states = []
    battery_heaters = []
    coil_voltages = {ax: [] for ax in coil_axes}
    coil_currents = {ax: [] for ax in coil_axes}
    batt_voltage = []
    batt_midpoint = []
    batt_current = []
    batt_soc = []
    batt_capacity = []
    batt_tte = []
    batt_temp = []
    jetson_power = []
    radio_power = []
    main_power = []
    peripheral_power = []

    # Compiled patterns
    ts_pat = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]")
    adcs_pat = re.compile(r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]\[INFO\] \[\d+\]\[ADCS\] .+:.+")
    cmd_global_pat = re.compile(r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]\[INFO\] \[\d+\]\[COMMAND\] GLOBAL STATE: .+")
    cmd_ram_pat = re.compile(r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]\[INFO\] \[\d+\]\[COMMAND\] RAM USAGE: .+")
    eps_pat = re.compile(r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]\[INFO\] \[\d+\]\[EPS\] .+")
    payload_pat = re.compile(r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]\[INFO\] \[\d+\]\[PAYLOAD\] Payload state: .+")

    with open(outfile, "r", encoding="latin-1") as f:
        for line in f:
            line = line.strip()

            # Update wall-clock reference from every timestamped line
            ts_m = ts_pat.match(line)
            if ts_m:
                wall_dt = datetime.strptime(ts_m.group(1), dt_format)
                if first_wall_time is None:
                    first_wall_time = wall_dt
                current_wall_t = (wall_dt - first_wall_time).total_seconds()

            # --- ADCS ---
            if adcs_pat.match(line):
                m = re.search(r"\[ADCS\] Time :\s+([\d.e+-]+)", line)
                if m:
                    continue  # time line only updates wall reference, no data stored

                m = re.search(r"ADCS Mode : (\d+)", line)
                if m:
                    adcs_modes.append([current_wall_t, int(m.group(1))])
                    continue

                m = re.search(r"Controller Mode : (\d+)", line)
                if m:
                    controller_modes.append([current_wall_t, int(m.group(1))])
                    continue

                m = re.search(r"Gyro Ang Vel : \[(.*?)\]", line)
                if m:
                    values = re.findall(r"np\.float64\((.*?)\)", m.group(1))
                    if not values:
                        values = re.findall(r"[-+]?\d*\.\d+(?:[eE][-+]?\d+)?|[-+]?\d+(?:[eE][-+]?\d+)?", m.group(1))
                    gyro_ang_vels.append([current_wall_t] + [float(v) for v in values])
                    continue

                m = re.search(r"Mag Field : \[(.*?)\]", line)
                if m:
                    values = re.findall(r"[-+]?\d*\.\d+(?:[eE][-+]?\d+)?|[-+]?\d+(?:[eE][-+]?\d+)?", m.group(1))
                    mag_fields.append([current_wall_t] + [float(v) for v in values])
                    continue

                m = re.search(r"Sun Vector : \[(.*?)\]", line)
                if m:
                    values = re.findall(r"[-+]?\d*\.\d+(?:[eE][-+]?\d+)?|[-+]?\d+(?:[eE][-+]?\d+)?", m.group(1))
                    sun_vectors.append([current_wall_t] + [float(v) for v in values])
                    continue

                m = re.search(r"Sun Status : (\d+)", line)
                if m:
                    sun_statuses.append([current_wall_t, int(m.group(1))])
                    continue

            # --- COMMAND ---
            elif cmd_global_pat.match(line):
                m = re.search(r"GLOBAL STATE: (\w+)", line)
                if m and m.group(1) in global_mode_code:
                    global_modes.append([current_wall_t, global_mode_code[m.group(1)]])

            elif cmd_ram_pat.match(line):
                m = re.search(r"RAM USAGE: (\d+)%", line)
                if m:
                    ram_usages.append([current_wall_t, int(m.group(1))])

            # --- EPS ---
            elif eps_pat.match(line):
                m = re.search(r"CPU temperature: (\d+)", line)
                if m:
                    cpu_temps.append([current_wall_t, int(m.group(1)) / 100.0])
                    continue

                m = re.search(r"EPS state: (\d+)", line)
                if m:
                    eps_states.append([current_wall_t, int(m.group(1))])
                    continue

                m = re.search(r"Battery Heaters Enabled: (\d+)", line)
                if m:
                    battery_heaters.append([current_wall_t, int(m.group(1))])
                    continue

                m = re.search(r"(XP|XM|YP|YM|ZP|ZM) Coil Voltage: ([-\d]+) mV, \w+ Coil Current: ([-\d]+) mA", line)
                if m:
                    ax, v, i = m.group(1), int(m.group(2)), int(m.group(3))
                    coil_voltages[ax].append([current_wall_t, v])
                    coil_currents[ax].append([current_wall_t, i])
                    continue

                m = re.search(r"Battery Pack Voltage: ([-\d]+) mV", line)
                if m:
                    batt_voltage.append([current_wall_t, int(m.group(1))])
                    continue

                m = re.search(r"Battery Pack Midpoint Voltage: ([-\d]+) mV", line)
                if m:
                    batt_midpoint.append([current_wall_t, int(m.group(1))])
                    continue

                m = re.search(r"Battery Pack Current: ([-\d]+) mA", line)
                if m:
                    batt_current.append([current_wall_t, int(m.group(1))])
                    continue

                m = re.search(r"Battery Pack Reported SOC: (\d+)%", line)
                if m:
                    batt_soc.append([current_wall_t, int(m.group(1))])
                    continue

                m = re.search(r"Battery Pack Reported Capacity: ([-\d]+) mAh", line)
                if m:
                    batt_capacity.append([current_wall_t, int(m.group(1))])
                    continue

                m = re.search(r"Battery Pack Time-to-Empty: ([-\d]+) seconds", line)
                if m:
                    batt_tte.append([current_wall_t, int(m.group(1))])
                    continue

                m = re.search(r"Battery Pack Temperature: (\d+)", line)
                if m:
                    batt_temp.append([current_wall_t, int(m.group(1)) / 100.0])
                    continue

                m = re.search(r"Jetson Voltage: ([-\d]+) mV, Jetson Current: ([-\d]+) mA", line)
                if m:
                    jetson_power.append([current_wall_t, int(m.group(1)), int(m.group(2))])
                    continue

                m = re.search(r"Radio Voltage: ([-\d]+) mV, Radio Current: ([-\d]+) mA", line)
                if m:
                    radio_power.append([current_wall_t, int(m.group(1)), int(m.group(2))])
                    continue

                m = re.search(r"Main Voltage: ([-\d]+) mV, Main Current: ([-\d]+) mA", line)
                if m:
                    main_power.append([current_wall_t, int(m.group(1)), int(m.group(2))])
                    continue

                m = re.search(r"Peripheral Voltage: ([-\d]+) mV, Peripheral Current: ([-\d]+) mA", line)
                if m:
                    peripheral_power.append([current_wall_t, int(m.group(1)), int(m.group(2))])
                    continue

            # --- PAYLOAD ---
            elif payload_pat.match(line):
                m = re.search(r"Payload state: (\w+)", line)
                if m:
                    payload_states.append([current_wall_t, payload_state_code.get(m.group(1), -1)])

    def to_np(lst):
        return np.array(lst) if lst else np.empty((0, 2))

    def to_np3(lst):
        return np.array(lst) if lst else np.empty((0, 3))

    adcs_modes_np = undersample(to_np(adcs_modes), 100 * percent_to_log)
    controller_modes_np = undersample(to_np(controller_modes), 100 * percent_to_log)
    global_modes_np = undersample(to_np(global_modes), 100 * percent_to_log)
    gyro_ang_vels_np = undersample(np.array(gyro_ang_vels) if gyro_ang_vels else np.empty((0, 4)), 100 * percent_to_log)
    mag_fields_np = undersample(np.array(mag_fields) if mag_fields else np.empty((0, 4)), 100 * percent_to_log)
    sun_vectors_np = undersample(np.array(sun_vectors) if sun_vectors else np.empty((0, 4)), 100 * percent_to_log)
    sun_statuses_np = undersample(to_np(sun_statuses), 100 * percent_to_log)
    cpu_temps_np = undersample(to_np(cpu_temps), 100 * percent_to_log)
    ram_usages_np = undersample(to_np(ram_usages), 100 * percent_to_log)
    payload_states_np = undersample(to_np(payload_states), 100 * percent_to_log)
    eps_states_np = undersample(to_np(eps_states), 100 * percent_to_log)
    battery_heaters_np = undersample(to_np(battery_heaters), 100 * percent_to_log)
    batt_voltage_np = undersample(to_np(batt_voltage), 100 * percent_to_log)
    batt_midpoint_np = undersample(to_np(batt_midpoint), 100 * percent_to_log)
    batt_current_np = undersample(to_np(batt_current), 100 * percent_to_log)
    batt_soc_np = undersample(to_np(batt_soc), 100 * percent_to_log)
    batt_capacity_np = undersample(to_np(batt_capacity), 100 * percent_to_log)
    batt_tte_np = undersample(to_np(batt_tte), 100 * percent_to_log)
    batt_temp_np = undersample(to_np(batt_temp), 100 * percent_to_log)
    jetson_power_np = undersample(to_np3(jetson_power), 100 * percent_to_log)
    radio_power_np = undersample(to_np3(radio_power), 100 * percent_to_log)
    main_power_np = undersample(to_np3(main_power), 100 * percent_to_log)
    peripheral_power_np = undersample(to_np3(peripheral_power), 100 * percent_to_log)

    coil_v = {ax: undersample(to_np(coil_voltages[ax]), 100 * percent_to_log) for ax in coil_axes}
    coil_i = {ax: undersample(to_np(coil_currents[ax]), 100 * percent_to_log) for ax in coil_axes}

    if not os.path.exists(result_folder_path):
        os.makedirs(result_folder_path)
    output_path = os.path.join(result_folder_path, "fsw_extracted_data.npz")
    np.savez(
        output_path,
        adcs_modes=adcs_modes_np,
        controller_modes=controller_modes_np,
        global_modes=global_modes_np,
        gyro_ang_vels=gyro_ang_vels_np,
        mag_fields=mag_fields_np,
        sun_vectors=sun_vectors_np,
        sun_statuses=sun_statuses_np,
        cpu_temps=cpu_temps_np,
        ram_usages=ram_usages_np,
        payload_states=payload_states_np,
        eps_states=eps_states_np,
        battery_heaters=battery_heaters_np,
        batt_voltage=batt_voltage_np,
        batt_midpoint=batt_midpoint_np,
        batt_current=batt_current_np,
        batt_soc=batt_soc_np,
        batt_capacity=batt_capacity_np,
        batt_tte=batt_tte_np,
        batt_temp=batt_temp_np,
        jetson_power=jetson_power_np,
        radio_power=radio_power_np,
        main_power=main_power_np,
        peripheral_power=peripheral_power_np,
        **{f"coil_v_{ax}": coil_v[ax] for ax in coil_axes},
        **{f"coil_i_{ax}": coil_i[ax] for ax in coil_axes},
    )
    print(f"Extracted data saved to {output_path}")

    if save_sil_logs:
        shutil.copy(outfile, result_folder_path)
    if erase_sil_logs:
        os.remove(outfile)


def _load(data, key, ncols=2):
    arr = data[key]
    if arr.ndim == 2 and arr.shape[0] > 0:
        return arr
    return np.empty((0, ncols))


def _plot_step(ax, arr, col, label=None, scale=1.0, **kwargs):
    """Plot a column from a 2-col-or-more array as a step series."""
    if arr.shape[0] == 0:
        return
    ax.plot(arr[:, 0], arr[:, col] * scale, drawstyle="steps-post", label=label, **kwargs)


def plot_ditl_FSW(ditl_folder_path):
    """
    Plots FSW data from a single DITL log folder.
    Expects fsw_extracted_data.npz to already exist in ditl_folder_path.
    """
    plots_folder_path = os.path.join(ditl_folder_path, "plots")
    os.makedirs(plots_folder_path, exist_ok=True)

    data_path = os.path.join(ditl_folder_path, "fsw_extracted_data.npz")
    if not os.path.exists(data_path):
        print(f"Extracted data file not found at {data_path}")
        return

    data = np.load(data_path, allow_pickle=True)
    print("Plotting DITL FSW data...")

    coil_axes = ["XP", "XM", "YP", "YM", "ZP", "ZM"]

    adcs_modes = _load(data, "adcs_modes")
    controller_modes = _load(data, "controller_modes")
    global_modes = _load(data, "global_modes")
    gyro_ang_vels = _load(data, "gyro_ang_vels", ncols=4)
    mag_fields = _load(data, "mag_fields", ncols=4)
    sun_vectors = _load(data, "sun_vectors", ncols=4)
    sun_statuses = _load(data, "sun_statuses")
    cpu_temps = _load(data, "cpu_temps")
    ram_usages = _load(data, "ram_usages")
    payload_states = _load(data, "payload_states")
    eps_states = _load(data, "eps_states")
    battery_heaters = _load(data, "battery_heaters")
    batt_voltage = _load(data, "batt_voltage")
    batt_midpoint = _load(data, "batt_midpoint")
    batt_current = _load(data, "batt_current")
    batt_soc = _load(data, "batt_soc")
    batt_capacity = _load(data, "batt_capacity")
    batt_tte = _load(data, "batt_tte")
    batt_temp = _load(data, "batt_temp")
    jetson_power = _load(data, "jetson_power", ncols=3)
    radio_power = _load(data, "radio_power", ncols=3)
    main_power = _load(data, "main_power", ncols=3)
    peripheral_power = _load(data, "peripheral_power", ncols=3)
    coil_v = {ax: _load(data, f"coil_v_{ax}") for ax in coil_axes}
    coil_i = {ax: _load(data, f"coil_i_{ax}") for ax in coil_axes}

    # Determine common x-axis bounds from all available data
    all_times = []
    for arr in [adcs_modes, controller_modes, global_modes, gyro_ang_vels, mag_fields,
                sun_vectors, sun_statuses, cpu_temps, ram_usages, payload_states,
                eps_states, battery_heaters, batt_voltage, batt_current, batt_soc,
                jetson_power, radio_power, main_power, peripheral_power,
                *coil_v.values(), *coil_i.values()]:
        if arr.shape[0] > 0:
            all_times.extend(arr[:, 0].tolist())
    xlim = (min(all_times), max(all_times)) if all_times else (0, 1)
    xlabel = "Time since log start (s)"

    # ── 1. ADCS Mode / Controller Mode / Global Mode ──────────────────────────
    mode_names = ["TUMBLING", "STABLE", "SUN_POINTED", "ACS_OFF"]
    ctrl_mode_names = ["BDOT", "B_cross", "PD_sun"]
    global_mode_names = ["STARTUP", "DETUMBLING", "NOMINAL", "EXPERIMENT", "LOW_POWER"]

    fig, axes = plt.subplots(3, 1, figsize=(14, 9), sharex=True)
    _plot_step(axes[0], adcs_modes, 1, marker=".")
    axes[0].set_yticks(range(len(mode_names)))
    axes[0].set_yticklabels(mode_names)
    axes[0].set_ylabel("ADCS Mode")
    axes[0].set_title("ADCS Mode")

    _plot_step(axes[1], controller_modes, 1, marker=".")
    axes[1].set_yticks(range(len(ctrl_mode_names)))
    axes[1].set_yticklabels(ctrl_mode_names)
    axes[1].set_ylabel("Controller Mode")
    axes[1].set_title("Controller Mode")

    _plot_step(axes[2], global_modes, 1, marker=".")
    axes[2].set_yticks(range(len(global_mode_names)))
    axes[2].set_yticklabels(global_mode_names)
    axes[2].set_ylabel("Global Mode")
    axes[2].set_xlabel(xlabel)
    axes[2].set_title("Global Mode")

    axes[0].set_xlim(xlim)
    plt.tight_layout()
    p = os.path.join(plots_folder_path, "fsw_modes_subplot.png")
    plt.savefig(p)
    plt.close()
    print(f"Modes subplot saved to {p}")

    # ── 2. Gyro Angular Velocity ───────────────────────────────────────────────
    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
    for i, label in enumerate(["Gyro X [deg/s]", "Gyro Y [deg/s]", "Gyro Z [deg/s]"]):
        _plot_step(axes[i], gyro_ang_vels, i + 1, scale=180.0 / np.pi, marker=".")
        axes[i].set_ylabel(label)
    axes[0].set_title("ADCS Angular Velocity")
    axes[2].set_xlabel(xlabel)
    axes[0].set_xlim(xlim)
    plt.tight_layout()
    p = os.path.join(plots_folder_path, "fsw_gyro_ang_vel_plot.png")
    plt.savefig(p)
    plt.close()
    print(f"Gyro Angular Velocity plot saved to {p}")

    # ── 3. Magnetic Field ──────────────────────────────────────────────────────
    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
    for i, label in enumerate(["Mag X [uT]", "Mag Y [uT]", "Mag Z [uT]"]):
        _plot_step(axes[i], mag_fields, i + 1, scale=1e6, marker=".")
        axes[i].set_ylabel(label)
    axes[0].set_title("ADCS Magnetic Field")
    axes[2].set_xlabel(xlabel)
    axes[0].set_xlim(xlim)
    plt.tight_layout()
    p = os.path.join(plots_folder_path, "fsw_mag_field_plot.png")
    plt.savefig(p)
    plt.close()
    print(f"Mag Field plot saved to {p}")

    # ── 4. Sun Vector ──────────────────────────────────────────────────────────
    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
    for i, label in enumerate(["Sun X", "Sun Y", "Sun Z"]):
        _plot_step(axes[i], sun_vectors, i + 1, marker=".")
        axes[i].set_ylabel(label)
    axes[0].set_title("ADCS Sun Vector")
    axes[2].set_xlabel(xlabel)
    axes[0].set_xlim(xlim)
    plt.tight_layout()
    p = os.path.join(plots_folder_path, "fsw_sun_vector_plot.png")
    plt.savefig(p)
    plt.close()
    print(f"Sun Vector plot saved to {p}")

    # ── 5. Sun Status ──────────────────────────────────────────────────────────
    sun_mode_names = ["SUN_FLAG_ZERO", "SUN_NO_READINGS", "SUN_NOT_ENOUGH_READINGS", "SUN_ECLIPSE"]
    plt.figure(figsize=(12, 4))
    if sun_statuses.shape[0] > 0:
        ss_plot = np.where(sun_statuses[:, 1] == 0, 50, sun_statuses[:, 1])
        plt.plot(sun_statuses[:, 0], ss_plot, marker=".", drawstyle="steps-post")
    plt.xlim(xlim)
    plt.ylabel("Sun Status")
    plt.xlabel(xlabel)
    plt.yticks(ticks=range(50, 50 + len(sun_mode_names)), labels=sun_mode_names)
    plt.ylim(49, 54)
    plt.title("ADCS Sun Status")
    plt.tight_layout()
    p = os.path.join(plots_folder_path, "fsw_sun_status_plot.png")
    plt.savefig(p)
    plt.close()
    print(f"Sun Status plot saved to {p}")

    # ── 6. CPU Temperature ────────────────────────────────────────────────────
    plt.figure(figsize=(12, 4))
    _plot_step(plt.gca(), cpu_temps, 1, marker=".", color="C1")
    plt.xlim(xlim)
    plt.ylabel("CPU Temperature [°C]")
    plt.xlabel(xlabel)
    plt.title("EPS CPU Temperature")
    plt.tight_layout()
    p = os.path.join(plots_folder_path, "fsw_cpu_temp_plot.png")
    plt.savefig(p)
    plt.close()
    print(f"CPU Temperature plot saved to {p}")

    # ── 7. RAM Usage ──────────────────────────────────────────────────────────
    plt.figure(figsize=(12, 4))
    _plot_step(plt.gca(), ram_usages, 1, marker=".", color="C2")
    plt.xlim(xlim)
    plt.ylabel("RAM Usage [%]")
    plt.xlabel(xlabel)
    plt.title("RAM Usage")
    plt.tight_layout()
    p = os.path.join(plots_folder_path, "fsw_ram_usage_plot.png")
    plt.savefig(p)
    plt.close()
    print(f"RAM Usage plot saved to {p}")

    # ── 8. Payload State ─────────────────────────────────────────────────────
    payload_state_names = ["OFF", "POWERING_ON", "READY", "SHUTTING_DOWN"]
    plt.figure(figsize=(12, 4))
    _plot_step(plt.gca(), payload_states, 1, marker=".", color="C3")
    plt.xlim(xlim)
    plt.ylabel("Payload State")
    plt.xlabel(xlabel)
    plt.yticks(ticks=range(len(payload_state_names)), labels=payload_state_names)
    plt.title("Payload State")
    plt.tight_layout()
    p = os.path.join(plots_folder_path, "fsw_payload_state_plot.png")
    plt.savefig(p)
    plt.close()
    print(f"Payload State plot saved to {p}")

    # ── 9. EPS State and Battery Heaters ─────────────────────────────────────
    fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    _plot_step(axes[0], eps_states, 1, marker=".", color="C4")
    axes[0].set_ylabel("EPS State")
    axes[0].set_title("EPS State")

    _plot_step(axes[1], battery_heaters, 1, marker=".", color="C5")
    axes[1].set_yticks([0, 1])
    axes[1].set_yticklabels(["Disabled", "Enabled"])
    axes[1].set_ylabel("Battery Heaters")
    axes[1].set_xlabel(xlabel)
    axes[1].set_title("Battery Heaters Enabled")

    axes[0].set_xlim(xlim)
    plt.tight_layout()
    p = os.path.join(plots_folder_path, "fsw_eps_state_plot.png")
    plt.savefig(p)
    plt.close()
    print(f"EPS State plot saved to {p}")

    # ── 10. Coil Voltages and Currents (6×2) ─────────────────────────────────
    fig, axes = plt.subplots(6, 2, figsize=(14, 18), sharex=True)
    for row, ax in enumerate(coil_axes):
        _plot_step(axes[row, 0], coil_v[ax], 1, marker=".")
        axes[row, 0].set_ylabel(f"{ax} [mV]")
        if row == 0:
            axes[row, 0].set_title("Coil Voltage")

        _plot_step(axes[row, 1], coil_i[ax], 1, marker=".")
        axes[row, 1].set_ylabel(f"{ax} [mA]")
        if row == 0:
            axes[row, 1].set_title("Coil Current")

    for col in range(2):
        axes[-1, col].set_xlabel(xlabel)
    axes[0, 0].set_xlim(xlim)
    plt.tight_layout()
    p = os.path.join(plots_folder_path, "fsw_coil_plot.png")
    plt.savefig(p)
    plt.close()
    print(f"Coil Voltages and Currents plot saved to {p}")

    # ── 11. Battery Pack (4×2) ────────────────────────────────────────────────
    batt_panels = [
        (batt_voltage,   1, "Voltage [mV]",       "Battery Pack Voltage"),
        (batt_current,   1, "Current [mA]",        "Battery Pack Current"),
        (batt_soc,       1, "SOC [%]",             "Reported SOC"),
        (batt_capacity,  1, "Capacity [mAh]",      "Reported Capacity"),
        (batt_temp,      1, "Temperature [°C]",    "Pack Temperature"),
        (batt_tte,       1, "Time-to-Empty [s]",   "Time to Empty"),
        (batt_midpoint,  1, "Midpoint V [mV]",     "Midpoint Voltage"),
        (battery_heaters,1, "Heaters Enabled",     "Battery Heaters"),
    ]
    fig, axes = plt.subplots(4, 2, figsize=(14, 14), sharex=True)
    for idx, (arr, col, ylabel, title) in enumerate(batt_panels):
        ax = axes[idx // 2, idx % 2]
        _plot_step(ax, arr, col, marker=".")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        if idx // 2 == 3:
            ax.set_xlabel(xlabel)
    axes[0, 0].set_xlim(xlim)
    plt.suptitle("Battery Pack", fontsize=14)
    plt.tight_layout()
    p = os.path.join(plots_folder_path, "fsw_battery_pack_plot.png")
    plt.savefig(p)
    plt.close()
    print(f"Battery Pack plot saved to {p}")

    # ── 12. Power Rails (4×2) ─────────────────────────────────────────────────
    rails = [
        (jetson_power,     "Jetson V [mV]",      "Jetson I [mA]",      "Jetson"),
        (radio_power,      "Radio V [mV]",       "Radio I [mA]",       "Radio"),
        (main_power,       "Main V [mV]",        "Main I [mA]",        "Main"),
        (peripheral_power, "Peripheral V [mV]",  "Peripheral I [mA]",  "Peripheral"),
    ]
    fig, axes = plt.subplots(4, 2, figsize=(14, 14), sharex=True)
    for row, (arr, v_label, i_label, name) in enumerate(rails):
        _plot_step(axes[row, 0], arr, 1, marker=".")
        axes[row, 0].set_ylabel(v_label)
        axes[row, 0].set_title(f"{name} Voltage")

        _plot_step(axes[row, 1], arr, 2, marker=".")
        axes[row, 1].set_ylabel(i_label)
        axes[row, 1].set_title(f"{name} Current")

    for col in range(2):
        axes[-1, col].set_xlabel(xlabel)
    axes[0, 0].set_xlim(xlim)
    plt.suptitle("Power Rails", fontsize=14)
    plt.tight_layout()
    p = os.path.join(plots_folder_path, "fsw_power_rails_plot.png")
    plt.savefig(p)
    plt.close()
    print(f"Power Rails plot saved to {p}")


if __name__ == "__main__":
    current_file_path = os.path.abspath(os.path.dirname(__file__))

    # List DITL log folders (subdirectories containing ditl.log)
    ditl_dirs = sorted(
        d for d in os.listdir(current_file_path)
        if os.path.isdir(os.path.join(current_file_path, d))
        and os.path.exists(os.path.join(current_file_path, d, "ditl.log"))
    )

    if not ditl_dirs:
        print(f"No DITL log folders found in {current_file_path}")
        sys.exit(0)

    print("Found DITL log folders:")
    id_width = max(len("ID"), len(str(len(ditl_dirs) - 1)))
    name_width = max(len("Folder"), max(len(d) for d in ditl_dirs))
    print(f"{'ID':>{id_width}}  {'Folder':<{name_width}}")
    print("-" * (id_width + 2 + name_width))
    for i, folder in enumerate(ditl_dirs):
        print(f"{i:>{id_width}}  {folder:<{name_width}}")

    folder_id = input("\nEnter the ID of the folder to plot: ")
    try:
        folder_id = int(folder_id)
        assert 0 <= folder_id < len(ditl_dirs)
    except (ValueError, AssertionError):
        print("Invalid ID. Exiting.")
        sys.exit(1)

    selected_folder = os.path.join(current_file_path, ditl_dirs[folder_id])
    log_path = os.path.join(selected_folder, "ditl.log")

    collect_FSW_data(log_path, selected_folder)
    plot_ditl_FSW(selected_folder)
