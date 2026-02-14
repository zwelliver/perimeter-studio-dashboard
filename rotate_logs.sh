#!/bin/bash
# ============================================
# Log Rotation for Perimeter Studio Automations
# ============================================
# Keeps one backup (.log.1) and truncates any log over the size limit.
# Designed to run weekly via cron.
#
# How it works:
#   1. Finds all .log files in the script directory
#   2. If a log exceeds MAX_SIZE_MB, rotates it:
#      - Moves current .log → .log.1 (overwriting any previous backup)
#      - Creates a fresh empty .log
#   3. Logs a summary of what it did
#
# Usage: ./rotate_logs.sh [--dry-run]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAX_SIZE_MB=5
MAX_SIZE_BYTES=$((MAX_SIZE_MB * 1024 * 1024))
DRY_RUN=false
ROTATED=0
SKIPPED=0

if [ "$1" = "--dry-run" ]; then
    DRY_RUN=true
    echo "[DRY RUN] No files will be modified."
    echo ""
fi

echo "=== Log Rotation $(date '+%Y-%m-%d %H:%M:%S') ==="
echo "Directory: $SCRIPT_DIR"
echo "Max size:  ${MAX_SIZE_MB} MB"
echo ""

for logfile in "$SCRIPT_DIR"/*.log; do
    [ -f "$logfile" ] || continue

    filename=$(basename "$logfile")
    size_bytes=$(stat -f%z "$logfile" 2>/dev/null || stat --printf="%s" "$logfile" 2>/dev/null)
    size_mb=$(echo "scale=1; $size_bytes / 1048576" | bc 2>/dev/null || echo "?")

    if [ "$size_bytes" -gt "$MAX_SIZE_BYTES" ]; then
        if [ "$DRY_RUN" = true ]; then
            echo "  WOULD ROTATE: $filename (${size_mb} MB)"
        else
            mv "$logfile" "${logfile}.1"
            touch "$logfile"
            echo "  ROTATED: $filename (${size_mb} MB → backup at ${filename}.1)"
        fi
        ROTATED=$((ROTATED + 1))
    else
        SKIPPED=$((SKIPPED + 1))
    fi
done

echo ""
echo "Done. Rotated: $ROTATED | Skipped (under ${MAX_SIZE_MB} MB): $SKIPPED"
