#!/bin/bash
set -e  # Exit on error

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

# === Run remote command ===
REMOTE_CMD="cd $DEST_PATH && ./run.sh"
echo "Running remote command: $REMOTE_CMD"
ssh "$DEST_USER@$DEST_HOST" "$REMOTE_CMD"

echo "Done!"
