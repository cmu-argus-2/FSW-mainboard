#!/bin/bash

TIMEOUT=$((1*3600))

DATE=$(date +%m_%d_%y_%H)

if (( TIMEOUT < 60 )); then
    TRIAL_LEN="${TIMEOUT}s"
elif (( TIMEOUT < 3600 )); then
    TRIAL_LEN="$(( TIMEOUT / 60 ))m"
else
    TRIAL_LEN="$(( TIMEOUT / 3600 ))h"
fi

LOG_DIR="ditl_logs/controller_mode_ditl_${DATE}_${TRIAL_LEN}"
LOG_FILE="${LOG_DIR}/ditl.log"
MINICOM_SCRIPT="tmp/ditl_minicom_script"

mkdir -p "$LOG_DIR"

{
    echo "Branch: $(git rev-parse --abbrev-ref HEAD)"
    echo "Commit: $(git log -1 --oneline)"
    echo ""
    git diff HEAD
} > "${LOG_DIR}/git_state.txt"

# Create minicom script to send ctrl+c and ctrl+d on startup
# chmod 644 "$MINICOM_SCRIPT"
cat > "$MINICOM_SCRIPT" << 'EOF'
send "^C"
sleep 1
send "^D"
sleep 1
EOF

sudo ./run.sh
sudo timeout "$TIMEOUT" minicom -D /dev/ttyACM0 -C "$LOG_FILE" -S "$MINICOM_SCRIPT"
echo "Log saved to $LOG_FILE"
