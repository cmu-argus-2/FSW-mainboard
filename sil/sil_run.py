import argparse
import collections.abc
import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime

import yaml

# flake8: noqa: E402
project_root = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.abspath(os.path.join(project_root, ".."))

# Add the project root to PYTHONPATH if it isn't already
if project_root not in sys.path:
    sys.path.append(project_root)
# from argusim.visualization.plotter import plot_all
from sil.fsw_plotter import collect_FSW_data, plot_FSW, plot_results

# DEFAULT_RUNTIME = 60  # 5 * 60  # 5 minutes
# DEFAULT_OUTFILE = "sil_logs.log"
# DEFAULT_N_TRIALS = 1  # Default number of trials to run
DEFAULT_CONFIGFILE = "sil_campaign_params.yaml"

# KEYWORD SEARCHES:
# List of all keywords to probe the log for
# Enter as a dictionary of KEYWORD - COLOR combos
KEYWORDS = {"WARNING": "\033[93m", "ERROR": "\033[91m"}


def FSW_simulate(runtime: float, outfile: str, trial_number: int, trial_date: str, sim_set_name: str) -> None:
    try:
        with open(outfile, "w") as log_file:
            # option to run a number of simulations, and to run a specific trial
            process = subprocess.Popen(
                ["./run.sh", "simulate", str(trial_number), trial_date, sim_set_name],
                stdout=log_file,
                stderr=log_file,
                preexec_fn=lambda: (os.setsid(), signal.alarm(20)),
            )
            print(f"Running simulation for {runtime} seconds, output written to {outfile}")
            time.sleep(runtime)
            print("Terminating...")
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)

    except Exception as e:
        print(f"Error: {e}")


def parse_FSW_logs(outfile):
    errors_detected = False
    with open(outfile, "r") as log_file:
        for line in log_file:
            for keyword in KEYWORDS.keys():
                if keyword in line:
                    print(f"{KEYWORDS[keyword]}{line}")
                    if keyword == "ERROR":
                        errors_detected = True

    if errors_detected:
        raise Exception("FSW Simulation Failed")


def update(d, u, i):
    """
    Recursively updates dictionary d with values from dictionary u.
    Solution based on https://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
    """
    if i > 10:
        raise Exception("Max recursion depth reached in update()")
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update(d.get(k, {}), v, i + 1)
        else:
            d[k] = v
    return d


def generate_sim_set_params(sim_set_config):  # , i_sim_set: int):
    # generate params.yaml for this sim set
    configs_folder_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "configs")
    nominal_config_file_path = os.path.join(configs_folder_path, "nominal_params.yaml")
    sim_set_config_file_path = os.path.join(configs_folder_path, "params.yaml")
    if os.path.exists(sim_set_config_file_path):
        os.remove(sim_set_config_file_path)
    shutil.copy(nominal_config_file_path, sim_set_config_file_path)

    if sim_set_config["param_changes"]:
        with open(sim_set_config_file_path, "r") as file:
            params_data = yaml.safe_load(file)

        params_data = update(params_data, sim_set_config["param_changes"], 0)

        with open(sim_set_config_file_path, "w") as file:
            yaml.dump(params_data, file)

    return sim_set_config


def run_simulation_trial(trial_number: int, trial_date: str, sim_set_name: str, set_config_params, args) -> None:

    # Run FSW Simulation
    FSW_simulate(
        int(set_config_params["runtime"]),
        set_config_params["outfile"],
        trial_number=trial_number,
        trial_date=trial_date,
        sim_set_name=sim_set_name,
    )
    # Collect FSW data
    trial_result_folder_path = os.path.join(
        current_file_path, "results", trial_date, sim_set_name, "trials", "trial" + str(trial_number)
    )
    os.makedirs(trial_result_folder_path, exist_ok=True)
    collect_FSW_data(
        set_config_params["outfile"],
        trial_result_folder_path,
        save_sil_logs=args.store_sil_logs_results,
        erase_sil_logs=args.erase_sil_logs,
        percent_to_log=set_config_params["fsw_percent_to_log"],
    )
    print(f"Trial {trial_number} of {sim_set_name} completed. Results saved to {trial_result_folder_path}")


def arg_parse(parser):
    parser.add_argument(
        "--sil_campaign_config_file",
        default=DEFAULT_CONFIGFILE,
        help=(
            "Path to sil campaign config file [string, default: "
            f"{DEFAULT_CONFIGFILE}] \n NOTE: Enter filename with extension"
        ),
    )
    parser.add_argument(
        "--erase_sil_logs",
        action="store_true",
        default=False,
        help="Flag to erase SIL logs in main folder [default: False]",
    )
    parser.add_argument(
        "--store_sil_logs_results",
        action="store_true",
        default=False,
        help="Flag to store SIL logs for each trial in results trial folder [default: False]",
    )

    # Parse Arguments
    return parser.parse_args()


if __name__ == "__main__":
    # Define Parser
    parser = argparse.ArgumentParser(prog="SIL_tester")

    args = arg_parse(parser)
    # args.store_sil_logs_results = False
    # args.erase_sil_logs = True

    trial_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    current_file_path = os.path.abspath(os.path.dirname(__file__))
    campaign_folder_path = os.path.join(current_file_path, "results", trial_date)
    campaign_config_file_path = os.path.join(current_file_path, "configs", args.sil_campaign_config_file)

    # Read sil campaign config to determine number of sim sets
    with open(campaign_config_file_path, "r") as file:
        sil_campaign_params = yaml.safe_load(file)
    sim_sets = sil_campaign_params["sil_campaign"]
    n_sim_sets = len(sim_sets.keys())

    # Run campaign script
    os.makedirs(campaign_folder_path)
    # Copy the campaign config file to the campaign folder
    shutil.copy(campaign_config_file_path, os.path.join(campaign_folder_path, "sil_campaign_params.yaml"))
    for sim_set in sim_sets.keys():
        print(f"Running Simulation Set {sim_set}...")
        # Generate sim set params file
        set_config_params = generate_sim_set_params(sil_campaign_params["sil_campaign"][sim_set])
        sim_set_folder_path = os.path.join(campaign_folder_path, sim_set)
        n_trials = sil_campaign_params["sil_campaign"][sim_set]["num_sims"]
        # Run simulation set script
        for i in range(n_trials):
            run_simulation_trial(
                trial_number=i + 1,
                trial_date=trial_date,
                sim_set_name=sim_set,
                set_config_params=set_config_params,
                args=args,
            )

        # Run Plotting (Sim states)
        sim_set_folder_path = os.path.join("sil/results", trial_date, sim_set)

        # Write description.txt
        description_file_path = os.path.join(sim_set_folder_path, "description.txt")
        with open(description_file_path, "w") as description_file:
            description_file.write(sil_campaign_params["sil_campaign"][sim_set]["description"])

        # os.path.join(campaign_folder_path, f"sil_set_{i_sim_set}")
        plot_results(result_folder_path=sim_set_folder_path)
        # plot_all(result_folder_path=result_folder_path)

        # Run Plotting (from Sim and FSW logs)
        plot_FSW(result_folder_path=sim_set_folder_path)

        # Parse Logs
        if args.store_sil_logs_results:
            for i in range(n_trials):
                trial_number = i + 1
                trial_result_folder_path = os.path.join(sim_set_folder_path, "trials/trial" + str(trial_number))
                parse_FSW_logs(os.path.join(trial_result_folder_path, set_config_params["outfile"]))
