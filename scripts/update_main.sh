#!/bin/bash
# update_main.sh - Inject or restore main.py on a connected CircuitPython device
#
# Usage:
#   ./update_main.sh inject <script.py> [-b /custom/board/path]
#   ./update_main.sh restore              [-b /custom/board/path]

set -e

INJECT_MARKER_START="# >>> INJECTED CODE >>>"
INJECT_MARKER_END="# <<< INJECTED CODE <<<"

get_board_path() {
    local system
    system="$(uname -s)"
    case "$system" in
        Linux)
            if [ "$(hostname)" = "raspberrypi" ]; then
                echo "/mnt/mainboard"
            else
                echo "/media/$(id -un)/ARGUS"
            fi
            ;;
        Darwin)
            echo "/Volumes/ARGUS"
            ;;
        MINGW*|CYGWIN*|MSYS*)
            echo "D:\\"
            ;;
        *)
            echo "Error: Unsupported system: $system" >&2
            exit 1
            ;;
    esac
}

usage() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  inject <script.py>   Wrap main.py in \"\"\" \"\"\" and append the given script"
    echo "  restore              Remove injected code and unwrap the original main.py"
    echo ""
    echo "Options:"
    echo "  -b, --board PATH     Override the auto-detected board mount path"
    echo ""
    echo "Examples:"
    echo "  $0 inject scripts/radio_test.py"
    echo "  $0 inject scripts/radio_test.py -b /media/user/ARGUS"
    echo "  $0 restore"
    exit 1
}

# --- Parse arguments ---
COMMAND=""
SCRIPT_PATH=""
BOARD_PATH_OVERRIDE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        inject)
            COMMAND="inject"
            shift
            if [[ $# -gt 0 && "$1" != -* ]]; then
                SCRIPT_PATH="$1"
                shift
            fi
            ;;
        restore)
            COMMAND="restore"
            shift
            ;;
        -b|--board)
            shift
            BOARD_PATH_OVERRIDE="$1"
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Error: Unknown argument: $1"
            usage
            ;;
    esac
done

[ -z "$COMMAND" ] && usage

# --- Resolve board path ---
if [ -n "$BOARD_PATH_OVERRIDE" ]; then
    BOARD_PATH="$BOARD_PATH_OVERRIDE"
else
    BOARD_PATH="$(get_board_path)"
fi

DEST="$BOARD_PATH/main.py"

if [ ! -d "$BOARD_PATH" ]; then
    echo "Error: Board not found at '$BOARD_PATH'. Is the device mounted?"
    exit 1
fi

if [ ! -f "$DEST" ]; then
    echo "Error: main.py not found at '$DEST'"
    exit 1
fi

# --- Commands ---
case "$COMMAND" in
    inject)
        if [ -z "$SCRIPT_PATH" ]; then
            echo "Error: 'inject' requires a script path."
            usage
        fi
        if [ ! -f "$SCRIPT_PATH" ]; then
            echo "Error: Script not found: '$SCRIPT_PATH'"
            exit 1
        fi
        if grep -qF "$INJECT_MARKER_START" "$DEST"; then
            echo "Error: main.py already contains injected code. Run 'restore' first."
            exit 1
        fi

        TMP="$(mktemp)"
        {
            printf '"""\n'
            cat "$DEST"
            printf '"""\n'
            printf '\n'
            printf '%s\n' "$INJECT_MARKER_START"
            cat "$SCRIPT_PATH"
            printf '\n%s\n' "$INJECT_MARKER_END"
        } > "$TMP"

        cp "$TMP" "$DEST"
        rm "$TMP"
        echo "Injected '$SCRIPT_PATH' into '$DEST'"
        ;;

    restore)
        if ! grep -qF "$INJECT_MARKER_START" "$DEST"; then
            echo "Error: No injected code found in '$DEST'."
            exit 1
        fi

        python3 - "$DEST" "$INJECT_MARKER_START" "$INJECT_MARKER_END" <<'PYEOF'
import sys

path, marker_start, marker_end = sys.argv[1], sys.argv[2], sys.argv[3]

with open(path, 'r') as f:
    content = f.read()

# Isolate the original block (everything before the inject marker)
marker_idx = content.index(marker_start)
original_block = content[:marker_idx].strip()

# Strip enclosing triple-quotes added during inject
if original_block.startswith('"""'):
    original_block = original_block[3:]
if original_block.endswith('"""'):
    original_block = original_block[:-3]

with open(path, 'w') as f:
    f.write(original_block.strip('\n') + '\n')

print(f"Restored original main.py at {path}")
PYEOF
        ;;
esac
