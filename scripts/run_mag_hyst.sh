#!/bin/bash
# run_mag_hyst.sh - Deploy mag_hyst.py and log minicom output.
#
# Usage:
#   bash scripts/run_mag_hyst.sh [-p serial_port] [-b board_path]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

LOG_FILE="$REPO_ROOT/mag_hyst.log"
MINICOM_SCRIPT="$REPO_ROOT/tmp/ditl_minicom_script"
TIMEOUT=$((2*60))

# Create minicom script to send ctrl+c and ctrl+d on startup
# chmod 644 "$MINICOM_SCRIPT"
cat > "$MINICOM_SCRIPT" << 'EOF'
send "^C"
sleep 1
send "^D"
sleep 1
EOF

# Inject mag_hyst.py as main.py
INJECT_ARGS=("inject" "$SCRIPT_DIR/mag_hyst.py")

sudo bash "$SCRIPT_DIR/update_main.sh" "${INJECT_ARGS[@]}"
# sudo rm -f /var/lock/LCK..ttyACM0
sudo timeout "$TIMEOUT" minicom -D /dev/ttyACM0 -C "$LOG_FILE" -S "$MINICOM_SCRIPT"
echo "Log saved to $LOG_FILE"

# Restore original main.py
RESTORE_ARGS=("restore")
if [ -n "$BOARD_PATH_OVERRIDE" ]; then
    RESTORE_ARGS+=("-b" "$BOARD_PATH_OVERRIDE")
fi
sudo bash "$SCRIPT_DIR/update_main.sh" "${RESTORE_ARGS[@]}"
