#!/bin/bash
set -e  # Exit on error

# === Configuration ===
SRC_DIR="PATH TO FSW REPO ON YOUR COMPUTER"
DEST_USER="REMOTE COMPUTER USERNAME"
DEST_HOST="REMOTE COMPUTER IP"
DEST_PATH="PATH TO FSW REPO ON REMOTE COMPUTER"
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
