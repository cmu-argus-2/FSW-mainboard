import argparse
import os
import signal
import subprocess
import time

# from argusim.visualization.plotter import plot_all
from fsw_plotter import plot_FSW, collect_FSW_data

DEFAULT_RUNTIME = 60 # 5 * 60  # 5 minutes
DEFAULT_OUTFILE = "sil_logs.log"

# KEYWORD SEARCHES:
# List of all keywords to probe the log for
# Enter as a dictionary of KEYWORD - COLOR combos
KEYWORDS = {"WARNING": "\033[93m", "ERROR": "\033[91m"}


def FSW_simulate(runtime: float, outfile: str) -> None:
    try:
        with open(outfile, "w") as log_file:
            process = subprocess.Popen(["./run.sh", "simulate"], stdout=log_file, stderr=log_file, preexec_fn=os.setsid)
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

    # Parse Arguments
    args = parser.parse_args()

    # Run script
    FSW_simulate(int(args.duration), args.outfile)
    result_folder_path = os.path.join("montecarlo/results", max(os.listdir("montecarlo/results")))
    collect_FSW_data(args.outfile,result_folder_path)

    # Run Plotting (Sim states)
    plot_results(result_folder_path=result_folder_path)
    # plot_all(result_folder_path=result_folder_path)

    # Run Plotting (from Sim and FSW logs)
    plot_FSW(result_folder_path=os.path.join(result_folder_path, "plots"))

    # Parse Logs
    parse_FSW_logs(args.outfile)