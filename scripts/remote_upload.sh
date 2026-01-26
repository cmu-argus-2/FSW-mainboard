#!/bin/bash
set -e  # Exit on error

# === Parse arguments ===
RUN_PROGRAM=true

for arg in "$@"; do
  case $arg in
    --no-program)
      RUN_PROGRAM=false
      shift
      ;;
  esac
done

# === Configuration ===
SRC_DIR="/home/$USER/schl/sat/argus/FSW-mainboard/"
DEST_USER="argus"
DEST_HOST="172.20.70.133"
DEST_PATH="/home/argus/FSW-mainboard/"
IGNORE_FILE=".rsyncignore"

# === Sync via rsync ===
echo "Syncing $SRC_DIR to $DEST_USER@$DEST_HOST:$DEST_PATH ..."
rsync -avz --itemize-changes \
  --exclude-from="$IGNORE_FILE" \
  --checksum \
  --no-owner --no-times --no-perms --no-group \
  "$SRC_DIR" \
  "$DEST_USER@$DEST_HOST:$DEST_PATH" \
  --info=stats2

echo "Sync complete."

# === Run remote command (optional) ===
REMOTE_CMD="cd $DEST_PATH && ./run.sh"

if [ "$RUN_PROGRAM" = true ]; then
  echo "Running remote command: $REMOTE_CMD"
  ssh "$DEST_USER@$DEST_HOST" "$REMOTE_CMD"
else
  echo "Skipping remote command due to --no-program flag"
fi

echo "Done!"