# Argus Software-In-The-Loop

This folder has the configuration files and the results folder for Software-In-The-Loop testing of the Argus mainboard flight software.

The SIL is initiated through the sil_run.py script. This script will generate a configs/params.yaml file by editing the provided nominal_params.yaml with the changes described in the sil_campaign_params.yaml.

The sil_campaign_params.yaml file provides a list of Monte Carlo simulations to be run. Each entry in the list describes the parameters to be edited in the nominal_params.yaml for the Monte Carlo campaign, a description of the campaign, the number of runs, how long to let the fsw run, the file to store the log to and the percent of logged data to store.

The ci_sil_campaign_params.yaml defines the list of simulations to run in the CI pipeline.

The results are stored in the results folder, and are identified by timestamp. For each campaign, the results of each set of simulations are stored separately, with the results split between a plots folder with the generated figures and a trials folder with the data. The params.yaml used to generate the simulation is also stored for reproducibility, along with the description. The sil_campaign_params.yaml is similarly stored in the campaign folder.

The params.yaml file is still kept in the configs folder so the run.sh command still works, though this file is rewritten each run, and nominally the sil_run.py rather than the command run.sh should be used to run simulations.