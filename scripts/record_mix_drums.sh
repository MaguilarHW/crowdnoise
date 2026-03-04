#!/usr/bin/env bash
# Record+ingest kick+hats, then run drums MVP mix from ingest.
# Calls record_and_ingest_drum_samples.sh then run_drums_mvp.sh --from-ingest.
#
# Usage:
#   ./scripts/record_mix_drums.sh --stems-dir DIR --drum-dir DIR [--out MP3]
#   ./scripts/record_mix_drums.sh --stems-dir DIR --drum-dir DIR --beep-only --out out.mp3

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

RECORD_SCRIPT="$REPO_ROOT/scripts/record_and_ingest_drum_samples.sh"
DRUMS_MVP_SCRIPT="$REPO_ROOT/scripts/run_drums_mvp.sh"

STEMS_DIR=""
DRUM_DIR=""
BEEP_ONLY=false
OUT_MP3="recreation.mp3"

usage() {
  echo "Usage: $0 --stems-dir DIR --drum-dir DIR [--beep-only] [--out MP3]"
  echo "  --stems-dir   Demucs stems dir (e.g. output/htdemucs_6s/SongTitle)"
  echo "  --drum-dir    Drum decomposition dir with kick_times.csv, hats_times.csv"
  echo "  --beep-only   Use sine beeps instead of recording kick+hats"
  echo "  --out         Output MP3 (default: recreation.mp3)"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case $1 in
    --stems-dir)  STEMS_DIR="$2"; shift 2 ;;
    --drum-dir)   DRUM_DIR="$2";  shift 2 ;;
    --beep-only)  BEEP_ONLY=true; shift 1 ;;
    --out)        OUT_MP3="$2";   shift 2 ;;
    -h|--help)    usage ;;
    *)            echo "Unknown option: $1"; usage ;;
  esac
done

if [[ -z "$STEMS_DIR" || -z "$DRUM_DIR" ]]; then
  echo "ERROR: --stems-dir and --drum-dir are required"
  usage
fi

# Step 1: record and ingest
BEEP_ARGS=()
$BEEP_ONLY && BEEP_ARGS=(--beep-only)
"$RECORD_SCRIPT" "${BEEP_ARGS[@]}"

# Step 2: run drums MVP from ingest
"$DRUMS_MVP_SCRIPT" --stems-dir "$STEMS_DIR" --drum-dir "$DRUM_DIR" --from-ingest --out "$OUT_MP3"

echo "Done: $OUT_MP3"
