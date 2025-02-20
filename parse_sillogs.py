log_filename = "sil_sim.log"
error_filename = "sil_err.log"

python_err = False
with open(log_filename, "r") as log_file, open(error_filename, "w") as error_log:
    for line in log_file:
        # errors running the SIL
        if "Traceback" in line:
            python_err = True
        if python_err:
            error_log.write(line)

if python_err:
    raise Exception("Python errors found, see error log.")
