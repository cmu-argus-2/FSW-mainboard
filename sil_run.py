import os
import signal
import subprocess
import time

log_filename = f"sil_sim.log"
# error_log_filename = f"{timestamp}_err.log"

try:
    with open(log_filename, "w") as log_file:
        process = subprocess.Popen(["./run.sh", "simulate"], stdout=log_file, stderr=log_file, preexec_fn=os.setsid)
        print(f"Running simulation for 120 seconds, output written to {log_filename}")
        time.sleep(30)
        print("terminating...")
        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        print("done")

except Exception as e:
    print(f"Error: {e}")
