import argparse
import os
import signal
import subprocess
import time
from datetime import datetime

# from argusim.visualization.plotter import plot_all
from fsw_plotter import collect_FSW_data, plot_FSW

DEFAULT_RUNTIME = 60  # 5 * 60  # 5 minutes
DEFAULT_OUTFILE = "sil_logs.log"
DEFAULT_N_TRIALS = 100  # Default number of trials to run

# KEYWORD SEARCHES:
# List of all keywords to probe the log for
# Enter as a dictionary of KEYWORD - COLOR combos
KEYWORDS = {"WARNING": "\033[93m", "ERROR": "\033[91m"}


def FSW_simulate(runtime: float, outfile: str, trial_number: int, trial_date: str) -> None:
    try:
        with open(outfile, "w") as log_file:
            # option to run a number of simulations, and to run a specific trial
            process = subprocess.Popen(
                ["./run.sh", "simulate", str(trial_number), trial_date], stdout=log_file, stderr=log_file, preexec_fn=os.setsid
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


def plot_results(result_folder_path):
    result_folder_path = "../../../" + result_folder_path
    plot_script_abs = os.path.join(os.path.dirname(__file__), "simulation/argusim/visualization/plotter.py")
    process = subprocess.Popen(["python3", plot_script_abs, result_folder_path], cwd=os.path.dirname(plot_script_abs))
    while process.poll() is None:  # wait while the plotting is finished
        time.sleep(0.1)
    return_code = process.returncode
    if return_code != 0:
        raise AssertionError(f"Plotting failed with code {return_code}")


if __name__ == "__main__":
    # Define Parser
    parser = argparse.ArgumentParser(prog="SIL_tester")

    # Add arguments
    parser.add_argument(
        "--duration",
        default=DEFAULT_RUNTIME,
        help=f"Duration (in seconds) to simulate FSW for [float, default: {DEFAULT_RUNTIME}s]",
    )
    parser.add_argument(
        "--outfile",
        default=DEFAULT_OUTFILE,
        help=f"Log file to save FSW logs to [string, default: {DEFAULT_OUTFILE}] \n NOTE: Enter filename with extension",
    )
    parser.add_argument(
        "--n_trials",
        type=int,
        default=DEFAULT_N_TRIALS,
        help="Number of trials to run [int, default: 100]",
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
    args = parser.parse_args()
    # args.store_sil_logs_results = False
    # args.erase_sil_logs = True

    trial_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    result_folder_path = os.path.join("montecarlo/results", trial_date)

    # Run script
    for i in range(args.n_trials):
        trial_number = i + 1
        trial_result_folder_path = os.path.join(result_folder_path, "trials/trial" + str(trial_number))
        print(f"Running Trial {trial_number}...")

        # Run FSW Simulation
        FSW_simulate(int(args.duration), args.outfile, trial_number=trial_number, trial_date=trial_date)

        # Collect FSW data
        collect_FSW_data(
            args.outfile,
            trial_result_folder_path,
            save_sil_logs=args.store_sil_logs_results,
            erase_sil_logs=args.erase_sil_logs,
        )
        print(f"Trial {trial_number} completed. Results saved to {trial_result_folder_path}")

    # Run Plotting (Sim states)
    plot_results(result_folder_path=result_folder_path)
    # plot_all(result_folder_path=result_folder_path)

    # Run Plotting (from Sim and FSW logs)
    plot_FSW(result_folder_path=result_folder_path)

    # Parse Logs
    if args.store_sil_logs_results:
        for i in range(args.n_trials):
            trial_number = i + 1
            trial_result_folder_path = os.path.join(result_folder_path, "trials/trial" + str(trial_number))
            parse_FSW_logs(os.path.join(trial_result_folder_path, args.outfile))
