#!/usr/bin/env bash
# One-command drums MVP: song + canonical one-shot → recreation MP3.
#
# Prerequisites:
#   - Demucs split already done (output/htdemucs_6s/<song>/drums.mp3 etc)
#   - isolate_drums.py --export-hits already run (kick_times.csv, hats_times.csv)
#   - User one-shot canonicalized (e.g. canonical/canonical.mp3 from ingest)
#
# Usage:
#   ./scripts/run_drums_mvp.sh \
#     --stems-dir output/htdemucs_6s/SongTitle \
#     --drum-dir output/trackDecomp/SongTitle/drum \
#     --one-shot path/to/canonical.mp3 \
#     --out recreation.mp3
#
# Or with a project root where layout is standard:
#   ./scripts/run_drums_mvp.sh --project output --song "Song Title" --one-shot canonical.mp3 --out out.mp3

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Defaults
STEMS_DIR=""
DRUM_DIR=""
ONE_SHOT=""
OUT_MP3="recreation.mp3"
NORMALIZE=false
DRY_RUN=false

usage() {
  echo "Usage: $0 --stems-dir DIR --drum-dir DIR --one-shot PATH [--out OUT.mp3] [--normalize] [--dry-run]"
  echo "  --stems-dir   Demucs stems dir (e.g. output/htdemucs_6s/SongTitle)"
  echo "  --drum-dir    Drum decomposition dir with kick_times.csv, hats_times.csv"
  echo "  --one-shot    Path to canonical user one-shot"
  echo "  --out         Output MP3 (default: recreation.mp3)"
  echo "  --normalize   Run loudness normalization on output"
  echo "  --dry-run     Only run placement report, no mix"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case $1 in
    --stems-dir)   STEMS_DIR="$2"; shift 2 ;;
    --drum-dir)    DRUM_DIR="$2";  shift 2 ;;
    --one-shot)    ONE_SHOT="$2";  shift 2 ;;
    --out)         OUT_MP3="$2";   shift 2 ;;
    --normalize)   NORMALIZE=true; shift 1 ;;
    --dry-run)     DRY_RUN=true;   shift 1 ;;
    -h|--help)     usage ;;
    *)             echo "Unknown option: $1"; usage ;;
  esac
done

if [[ -z "$STEMS_DIR" || -z "$DRUM_DIR" || -z "$ONE_SHOT" ]]; then
  echo "ERROR: --stems-dir, --drum-dir, and --one-shot are required"
  usage
fi

STEMS_DIR="$(cd "$STEMS_DIR" && pwd)"
DRUM_DIR="$(cd "$DRUM_DIR" && pwd)"
ONE_SHOT="$(cd "$(dirname "$ONE_SHOT")" && pwd)/$(basename "$ONE_SHOT")"

KICK_CSV="$DRUM_DIR/kick_times.csv"
HATS_CSV="$DRUM_DIR/hats_times.csv"

if [[ ! -f "$KICK_CSV" || ! -f "$HATS_CSV" ]]; then
  echo "ERROR: kick_times.csv and hats_times.csv not found in $DRUM_DIR"
  echo "Run: python3 src/isolate_drums.py $STEMS_DIR/drums.mp3 --export-hits --out-dir output/trackDecomp"
  exit 1
fi

if [[ ! -f "$ONE_SHOT" ]]; then
  echo "ERROR: One-shot not found: $ONE_SHOT"
  exit 1
fi

DRUMS_STEM="$STEMS_DIR/drums.mp3"
if [[ ! -f "$DRUMS_STEM" ]]; then
  echo "ERROR: Drums stem not found: $DRUMS_STEM"
  exit 1
fi

# Build placements JSON
PLACEMENTS_JSON="$STEMS_DIR/drum_events.json"
echo "Building placements..."
python3 src/build_drum_placements.py \
  --kick-times "$KICK_CSV" \
  --hats-times "$HATS_CSV" \
  --one-shot "$ONE_SHOT" \
  --out "$PLACEMENTS_JSON"

# Dry-run report
echo ""
python3 scripts/dry_run_drum_report.py \
  --kick-times "$KICK_CSV" \
  --hats-times "$HATS_CSV" \
  2>/dev/null || true

if $DRY_RUN; then
  echo "Dry-run complete. Exiting."
  exit 0
fi

# Build mix config (merge Song_State structure with drum_mask)
MIX_CONFIG="$STEMS_DIR/drums_mvp_mix.json"
python3 << PYEOF
import json
import subprocess
import os

stems_dir = "$STEMS_DIR".replace("\\\\", "/")
one_shot = "$ONE_SHOT".replace("\\\\", "/")
drums_stem = stems_dir + "/drums.mp3"

# Get song length from drums stem
try:
  r = subprocess.run(
    ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", drums_stem],
    capture_output=True, text=True, check=True,
  )
  d = float(json.loads(r.stdout).get("format", {}).get("duration", 0))
  song_len_ms = int(d * 1000)
except Exception:
  song_len_ms = 300000

with open("$PLACEMENTS_JSON") as f:
  placements = json.load(f)

instruments = {
  "drums": {
    "active_path": drums_stem,
    "original_path": drums_stem,
  },
}
for name in ["bass", "other", "vocals"]:
  p = os.path.join(stems_dir, name + ".mp3")
  if os.path.exists(p):
    instruments[name] = {"active_path": p, "original_path": p}

config = {
  "song_length_ms": song_len_ms,
  "sr": 48000,
  "instruments": instruments,
  "drum_mask": {
    "one_shot_path": one_shot,
    "drum_events": placements["drum_events"],
  },
}
with open("$MIX_CONFIG", "w") as f:
  json.dump(config, f, indent=2)
PYEOF

# Run mixer
echo ""
echo "Running mix..."
MIX_CLI="$REPO_ROOT/bin/mix_json_cli"
if [[ ! -x "$MIX_CLI" ]]; then
  make
fi
"$MIX_CLI" "$MIX_CONFIG" "$OUT_MP3"

if $NORMALIZE; then
  TMP="$OUT_MP3.tmp.mp3"
  bash scripts/normalize_loudness.sh "$OUT_MP3" "$TMP"
  mv "$TMP" "$OUT_MP3"
  echo "Normalized: $OUT_MP3"
fi

echo "Done: $OUT_MP3"
