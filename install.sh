# Virtual Env setup
python3 -m venv .venv --system-site-packages
source .venv/bin/activate

# C++ sim setup
cd simulation
sh install.sh
cd ../

# Copy the montecarlo folder into FSW to store results
# Make a Results directory and copy the params.yaml file
# On the first run, the C++ default yaml file runs. For later runs, this file can be changed
mkdir -p results/
if ! test -f ./params.yaml; then
    cp ./simulation/montecarlo/configs/params.yaml ./
fi


