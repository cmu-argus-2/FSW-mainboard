import argparse
import os
import signal
import subprocess
import time

from argusim.visualization.plotter import plot_all

DEFAULT_RUNTIME = 5 * 60  # 5 minutes
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

    # Run Plotting
    result_folder_path = os.path.join("results", max(os.listdir("results")))
    plot_all(result_folder_path=result_folder_path)

    # Parse Logs
    parse_FSW_logs(args.outfile)
