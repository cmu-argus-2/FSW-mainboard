import argparse
import atexit
import collections.abc
import multiprocessing
import os
import shutil
import signal
import subprocess
import sys
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
DEFAULT_CONFIGFILE = "ci_sil_campaign_params.yaml"
STARTUP_OVERHEAD_S = 60.0  # wall-clock budget for build-emulator.py before main.py starts

# Module-level handle to the active simulation process so atexit and SIGTERM can clean it up.
_active_process: "subprocess.Popen | None" = None


def _cleanup_active_process() -> None:
    """Kill the active sim subprocess on exit to prevent orphaned processes."""
    if _active_process is not None and _active_process.poll() is None:
        try:
            os.killpg(os.getpgid(_active_process.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass


atexit.register(_cleanup_active_process)
signal.signal(signal.SIGTERM, lambda *_: sys.exit(1))  # ensure atexit runs on SIGTERM

# KEYWORD SEARCHES:
# List of all keywords to probe the log for
# Enter as a dictionary of KEYWORD - COLOR combos
KEYWORDS = {"WARNING": "\033[93m", "ERROR": "\033[91m"}


def FSW_simulate(
    max_sim_time: float,
    outfile: str,
    trial_number: int,
    trial_date: str,
    sim_set_name: str,
    sim_real_speedup=None,
    worker_id: int = 0,
) -> None:
    # The FSW process exits naturally via SimulationComplete when MAX_TIME is reached (exit code 0).
    # TimeoutExpired means the process hung and is a genuine error.
    global _active_process
    if sim_real_speedup is not None:
        safety_timeout = STARTUP_OVERHEAD_S + max_sim_time / sim_real_speedup * 2
    else:
        safety_timeout = STARTUP_OVERHEAD_S + max_sim_time / 50
    try:
        with open(outfile, "w") as log_file:
            cmd = ["./run.sh", "simulate", str(trial_number), trial_date, sim_set_name]
            cmd.append(str(sim_real_speedup) if sim_real_speedup is not None else "")
            cmd.append(str(worker_id))
            # option to run a number of simulations, and to run a specific trial
            process = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=log_file,
                start_new_session=True,
            )
            _active_process = process
            print(
                f"[worker {worker_id}] Running simulation: trial {trial_number}, "
                f"MAX_TIME={max_sim_time}s at {sim_real_speedup}x speedup, output written to {outfile}"
            )
            try:
                process.wait(timeout=safety_timeout)
                if process.returncode != 0:
                    raise RuntimeError(f"Simulation process exited with error (code {process.returncode})")
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                process.wait()
                raise RuntimeError(
                    f"Simulation hung: did not complete within {safety_timeout:.0f}s "
                    f"(MAX_TIME={max_sim_time}s, speedup={sim_real_speedup}x)"
                )
            except (KeyboardInterrupt, SystemExit):
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                process.wait()
                raise
    except RuntimeError:
        raise
    except Exception as e:
        print(f"Error running sim: {e}")
    finally:
        _active_process = None


def parse_FSW_logs(outfile):
    errors_detected = False
    error_logs = []
    with open(outfile, "r") as log_file:
        for line in log_file:
            for keyword in KEYWORDS.keys():
                if keyword in line:
                    print(f"{KEYWORDS[keyword]}{line}")
                    if keyword == "ERROR":
                        errors_detected = True
                        error_logs.append(line)

    if errors_detected:
        raise Exception(f"FSW Simulation Failed. Errors:\n{''.join(error_logs)}")


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
        try:
            with open(sim_set_config_file_path, "r") as file:
                params_data = yaml.safe_load(file)
        except Exception as e:
            raise Exception(f"Error reading nominal_params.yaml: {e}")

        params_data = update(params_data, sim_set_config["param_changes"], 0)
        try:
            with open(sim_set_config_file_path, "w") as file:
                yaml.dump(params_data, file)
        except Exception as e:
            raise Exception(f"Error writing params.yaml: {e}")

    return sim_set_config


def update_fsw_config(sim_set_config):
    param_changes = sim_set_config["fsw_config_param_changes"]
    if not param_changes:
        return
    fsw_config_file_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "..", "flight", "configuration", "ground.yaml"
    )
    # copy and replace ground_temp.yaml with the old values
    temp_config_file_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "..", "flight", "configuration", "ground_temp.yaml"
    )
    if not os.path.exists(temp_config_file_path):
        shutil.copy(fsw_config_file_path, temp_config_file_path)

    with open(fsw_config_file_path, "r") as file:
        config_data = yaml.safe_load(file)

    config_data = update(config_data, param_changes, 0)

    with open(fsw_config_file_path, "w") as file:
        yaml.dump(config_data, file)


def reset_fsw_config():
    fsw_config_file_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "..", "flight", "configuration", "ground.yaml"
    )
    temp_config_file_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "..", "flight", "configuration", "ground_temp.yaml"
    )
    if os.path.exists(temp_config_file_path):
        shutil.copy(temp_config_file_path, fsw_config_file_path)
        os.remove(temp_config_file_path)


def run_simulation_trial(
    trial_number: int,
    trial_date: str,
    sim_set_name: str,
    sim_real_speedup,
    max_sim_time: float,
    set_config_params,
    args,
    sil_path: str,
    worker_id: int = 0,
) -> float:
    """Returns wall-clock elapsed time for the trial in seconds."""
    trial_start = datetime.now()

    # Per-trial log file so parallel workers never share a log
    outfile = f"sil_logs_trial{trial_number}.log"

    # Run FSW Simulation
    FSW_simulate(
        max_sim_time=max_sim_time,
        outfile=outfile,
        trial_number=trial_number,
        trial_date=trial_date,
        sim_set_name=sim_set_name,
        sim_real_speedup=sim_real_speedup,
        worker_id=worker_id,
    )

    # Collect FSW data
    trial_result_folder_path = os.path.join(
        sil_path, "results", trial_date, sim_set_name, "trials", "trial" + str(trial_number)
    )
    os.makedirs(trial_result_folder_path, exist_ok=True)

    # Copy the worker's sd/ folder to the trial result, then delete the worker build dir
    if worker_id > 0:
        build_dir = os.path.join(sil_path, "..", f"build_{worker_id}")
        sd_src = os.path.join(build_dir, "sd")
        if os.path.exists(sd_src):
            shutil.copytree(sd_src, os.path.join(trial_result_folder_path, "sd"), dirs_exist_ok=True)
        shutil.rmtree(build_dir, ignore_errors=True)

    collect_FSW_data(
        outfile,
        trial_result_folder_path,
        save_sil_logs=args.store_sil_logs_results,
        erase_sil_logs=args.erase_sil_logs,
        percent_to_log=set_config_params["fsw_percent_to_log"],
    )
    elapsed = (datetime.now() - trial_start).total_seconds()
    print(f"[worker {worker_id}] Trial {trial_number} of {sim_set_name} completed in {elapsed:.1f}s.")
    return elapsed


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
        default=True,
        help="Flag to erase SIL logs in main folder [default: True]",
    )
    parser.add_argument(
        "--store_sil_logs_results",
        action="store_true",
        default=False,
        help="Flag to store SIL logs for each trial in results trial folder [default: False]",
    )
    parser.add_argument(
        "--multiprocessing",
        action="store_true",
        default=True,
        help="Run trials in parallel using multiprocessing (workers = min(n_trials, cpu_count))",
    )
    parser.add_argument(
        "--max_workers",
        type=int,
        default=min(10, os.cpu_count() or 1),
        help="Upper bound on the number of parallel processes to use for simulations [default: 10 or cpu_count if lower]",
    )

    # Parse Arguments
    return parser.parse_args()


# Per-worker global set by _init_worker; used by run_simulation_trial_worker.
_worker_id: int = 0


def _init_worker(id_queue: multiprocessing.Queue) -> None:
    """Pool initializer: each worker process claims a unique ID from the queue."""
    global _worker_id
    _worker_id = id_queue.get()


def run_simulation_trial_worker(
    trial_number: int,
    trial_date: str,
    sim_set_name: str,
    sim_real_speedup,
    max_sim_time: float,
    set_config_params,
    args,
    sil_path: str,
) -> float:
    """Thin wrapper used by Pool.starmap so worker_id comes from the process-local global."""
    return run_simulation_trial(
        trial_number=trial_number,
        trial_date=trial_date,
        sim_set_name=sim_set_name,
        sim_real_speedup=sim_real_speedup,
        max_sim_time=max_sim_time,
        set_config_params=set_config_params,
        args=args,
        sil_path=sil_path,
        worker_id=_worker_id,
    )


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

    # Capture git diff and git status to track code version
    project_root_path = os.path.join(current_file_path, "..")
    git_diff_path = os.path.join(campaign_folder_path, "git.txt")

    try:
        # Capture git diff
        with open(git_diff_path, "w") as f:
            subprocess.run(
                ["git", "status"],
                cwd=project_root_path,
                stdout=f,
                stderr=subprocess.STDOUT,
                text=True,
            )
            subprocess.run(
                ["git", "diff"],
                cwd=project_root_path,
                stdout=f,
                stderr=subprocess.STDOUT,
                text=True,
            )
    except Exception as e:
        print(f"Warning: Could not capture git information: {e}")

    # Copy the campaign config file to the campaign folder
    shutil.copy(campaign_config_file_path, os.path.join(campaign_folder_path, "sil_campaign_params.yaml"))
    for sim_set in sim_sets.keys():
        # Generate sim set params file
        set_config_params = generate_sim_set_params(sil_campaign_params["sil_campaign"][sim_set])
        sim_set_folder_path = os.path.join(campaign_folder_path, sim_set)
        n_trials = sil_campaign_params["sil_campaign"][sim_set]["num_sims"]
        first_trial_id = sil_campaign_params["sil_campaign"][sim_set]["first_trial_number"]
        max_n_workers = args.max_workers
        n_workers = min(n_trials, max_n_workers) if args.multiprocessing else 1

        print(f"Running Simulation Set {sim_set} ({n_workers} worker(s))...")

        sim_real_speedup = sil_campaign_params["sil_campaign"][sim_set].get("sim_real_speedup", None)

        param_changes = set_config_params.get("param_changes") or {}
        if "MAX_TIME" in param_changes:
            max_sim_time = param_changes["MAX_TIME"]
        else:
            params_yaml_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "configs", "params.yaml")
            with open(params_yaml_path) as f:
                max_sim_time = yaml.safe_load(f)["MAX_TIME"]
            print(f"[{sim_set}] No MAX_TIME in param_changes, using nominal MAX_TIME={max_sim_time}s from params.yaml")

        # Update the fsw config.yaml
        update_fsw_config(sil_campaign_params["sil_campaign"][sim_set])

        try:
            # Run simulation set script
            # Build the trial args list (same for both sequential and parallel paths)
            trial_args = [
                (
                    i + first_trial_id,
                    trial_date,
                    sim_set,
                    sim_real_speedup,
                    max_sim_time,
                    set_config_params,
                    args,
                    current_file_path,
                )
                for i in range(n_trials)
            ]

            # Run simulation set — sequential if n_workers == 1, parallel otherwise
            if n_workers == 1:
                elapsed_times = [run_simulation_trial_worker(*t_args) for t_args in trial_args]
            else:
                # Assign worker IDs 1..n_workers via a Queue so each Pool process gets a stable ID.
                id_queue: multiprocessing.Queue = multiprocessing.Queue()
                for k in range(1, n_workers + 1):
                    id_queue.put(k)
                with multiprocessing.Pool(n_workers, initializer=_init_worker, initargs=(id_queue,)) as pool:
                    elapsed_times = pool.starmap(run_simulation_trial_worker, trial_args)

            trial_times = list(zip([i + first_trial_id for i in range(n_trials)], elapsed_times))

        finally:
            #  reset fsw config and delete temp config file
            reset_fsw_config()

        # Run Plotting (Sim states)
        sim_set_folder_path = os.path.join("sil/results", trial_date, sim_set)

        # Write description.txt
        description_file_path = os.path.join(sim_set_folder_path, "description.txt")
        with open(description_file_path, "w") as description_file:
            description_file.write(sil_campaign_params["sil_campaign"][sim_set]["description"])

        # Write timing.txt
        times = [t for _, t in trial_times]
        timing_file_path = os.path.join(sim_set_folder_path, "timing.txt")
        with open(timing_file_path, "w") as f:
            f.write(f"Sim set : {sim_set}\n")
            f.write(
                f"MAX_TIME: {max_sim_time}s | speedup: {f'{sim_real_speedup}x' if sim_real_speedup is not None else 'full CPU'} | trials: {n_trials}\n"
            )
            f.write("-" * 40 + "\n")
            for trial_num, t in trial_times:
                f.write(f"trial {trial_num:>4d}: {t:>8.1f}s\n")
            f.write("-" * 40 + "\n")
            f.write(f"total   : {sum(times):>8.1f}s\n")
            f.write(f"mean    : {sum(times)/len(times):>8.1f}s\n")
            f.write(f"min     : {min(times):>8.1f}s\n")
            f.write(f"max     : {max(times):>8.1f}s\n")

        # os.path.join(campaign_folder_path, f"sil_set_{i_sim_set}")
        plot_results(result_folder_path=sim_set_folder_path)
        # plot_all(result_folder_path=result_folder_path)

        # Run Plotting (from Sim and FSW logs)
        plot_FSW(result_folder_path=sim_set_folder_path)

        # Parse Logs
        if args.store_sil_logs_results:
            for i in range(n_trials):
                trial_number = i + first_trial_id
                trial_result_folder_path = os.path.join(sim_set_folder_path, "trials/trial" + str(trial_number))
                parse_FSW_logs(os.path.join(trial_result_folder_path, f"sil_logs_trial{trial_number}.log"))
