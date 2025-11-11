# Virtual Env setup
python3 -m venv .venv --system-site-packages
source .venv/bin/activate

# C++ sim setup
cd simulation
sh install.sh
cd ../