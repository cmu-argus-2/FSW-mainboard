import argparse
import os
import signal
import subprocess
import time
import warnings

DEFAULT_RUNTIME = 5 * 60  # 5 minutes
DEFAULT_OUTFILE = "sil_logs.log"


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

    with open(outfile, "r") as log_file:
        for line in log_file:
            if "WARNING" in line:
                warnings.warn(line)
            if "ERROR" in line:
                raise Exception(f"Error detected at {line}")


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

    # Parse Logs
    parse_FSW_logs()
