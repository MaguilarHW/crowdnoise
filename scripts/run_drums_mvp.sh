#!/usr/bin/env bash
# One-command drums MVP: song + canonical one-shot(s) → recreation MP3.
#
# Prerequisites:
#   - Demucs split already done (output/htdemucs_6s/<song>/drums.mp3 etc)
#   - isolate_drums.py --export-hits already run (kick_times.csv, hats_times.csv)
#   - User one-shot(s) canonicalized (e.g. canonical/canonical.mp3 from ingest)
#
# Usage:
#   ./scripts/run_drums_mvp.sh \
#     --stems-dir output/htdemucs_6s/SongTitle \
#     --drum-dir output/trackDecomp/SongTitle/drum \
#     --one-shot path/to/canonical.mp3 \
#     --out recreation.mp3
#
# With --from-ingest: read kick_canonical, hats_canonical from recorded_samples/ingest_result.json
# With --kick-shot/--hats-shot: separate one-shots for kick and hats
# Require: ONE_SHOT or KICK_SHOT or HATS_SHOT (at least one)

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Defaults
STEMS_DIR=""
DRUM_DIR=""
ONE_SHOT=""
KICK_SHOT=""
HATS_SHOT=""
FROM_INGEST=false
OUT_MP3="recreation.mp3"
NORMALIZE=false
DRY_RUN=false

usage() {
  echo "Usage: $0 --stems-dir DIR --drum-dir DIR (--one-shot PATH | --kick-shot PATH | --hats-shot PATH | --from-ingest) [options]"
  echo "  --stems-dir   Demucs stems dir (e.g. output/htdemucs_6s/SongTitle)"
  echo "  --drum-dir    Drum decomposition dir with kick_times.csv, hats_times.csv"
  echo "  --one-shot    Path to canonical user one-shot (single for both kick+hats)"
  echo "  --kick-shot   Path to kick one-shot"
  echo "  --hats-shot   Path to hats one-shot"
  echo "  --from-ingest Read kick_canonical, hats_canonical from recorded_samples/ingest_result.json"
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
    --kick-shot)   KICK_SHOT="$2"; shift 2 ;;
    --hats-shot)   HATS_SHOT="$2"; shift 2 ;;
    --from-ingest) FROM_INGEST=true; shift 1 ;;
    --out)         OUT_MP3="$2";   shift 2 ;;
    --normalize)   NORMALIZE=true; shift 1 ;;
    --dry-run)     DRY_RUN=true;   shift 1 ;;
    -h|--help)     usage ;;
    *)             echo "Unknown option: $1"; usage ;;
  esac
done

if [[ -z "$STEMS_DIR" || -z "$DRUM_DIR" ]]; then
  echo "ERROR: --stems-dir and --drum-dir are required"
  usage
fi

# --from-ingest: read kick_canonical, hats_canonical from ingest_result.json
if $FROM_INGEST; then
  INGEST_JSON="$REPO_ROOT/recorded_samples/ingest_result.json"
  if [[ ! -f "$INGEST_JSON" ]]; then
    echo "ERROR: --from-ingest requires recorded_samples/ingest_result.json"
    exit 1
  fi
  KICK_CANONICAL=$(python3 -c "import json; d=json.load(open('$INGEST_JSON')); print(d.get('kick_canonical','') or '')")
  HATS_CANONICAL=$(python3 -c "import json; d=json.load(open('$INGEST_JSON')); print(d.get('hats_canonical','') or '')")
  if [[ -n "$KICK_CANONICAL" ]]; then
    KICK_SHOT="${KICK_SHOT:-$KICK_CANONICAL}"
  fi
  if [[ -n "$HATS_CANONICAL" ]]; then
    HATS_SHOT="${HATS_SHOT:-$HATS_CANONICAL}"
  fi
  # Fallback: when only one present, use ONE_SHOT for the missing one
  if [[ -n "$ONE_SHOT" ]]; then
    [[ -z "$KICK_SHOT" ]] && KICK_SHOT="$ONE_SHOT"
    [[ -z "$HATS_SHOT" ]] && HATS_SHOT="$ONE_SHOT"
  fi
fi

# Require at least one shot source
if [[ -z "$ONE_SHOT" && -z "$KICK_SHOT" && -z "$HATS_SHOT" ]]; then
  echo "ERROR: Provide --one-shot, or --kick-shot, or --hats-shot, or --from-ingest"
  usage
fi

STEMS_DIR="$(cd "$STEMS_DIR" && pwd)"
DRUM_DIR="$(cd "$DRUM_DIR" && pwd)"

_resolve_path() {
  local p="$1"
  [[ -z "$p" ]] && return
  if [[ -f "$p" ]]; then
    echo "$(cd "$(dirname "$p")" && pwd)/$(basename "$p")"
  else
    local abs="$REPO_ROOT/$p"
    if [[ -f "$abs" ]]; then
      echo "$(cd "$(dirname "$abs")" && pwd)/$(basename "$abs")"
    else
      local abs2="$REPO_ROOT/recorded_samples/$p"
      if [[ -f "$abs2" ]]; then
        echo "$(cd "$(dirname "$abs2")" && pwd)/$(basename "$abs2")"
      else
        echo "$p"
      fi
    fi
  fi
}

[[ -n "$ONE_SHOT" ]] && ONE_SHOT="$(_resolve_path "$ONE_SHOT")"
[[ -n "$KICK_SHOT" ]] && KICK_SHOT="$(_resolve_path "$KICK_SHOT")"
[[ -n "$HATS_SHOT" ]] && HATS_SHOT="$(_resolve_path "$HATS_SHOT")"

KICK_CSV="$DRUM_DIR/kick_times.csv"
HATS_CSV="$DRUM_DIR/hats_times.csv"

if [[ ! -f "$KICK_CSV" || ! -f "$HATS_CSV" ]]; then
  echo "ERROR: kick_times.csv and hats_times.csv not found in $DRUM_DIR"
  echo "Run: python3 src/isolate_drums.py $STEMS_DIR/drums.mp3 --export-hits --out-dir output/trackDecomp"
  exit 1
fi

# Validate shot files
if [[ -n "$ONE_SHOT" && ! -f "$ONE_SHOT" ]]; then
  echo "ERROR: One-shot not found: $ONE_SHOT"
  exit 1
fi
if [[ -n "$KICK_SHOT" && ! -f "$KICK_SHOT" ]]; then
  echo "ERROR: Kick shot not found: $KICK_SHOT"
  exit 1
fi
if [[ -n "$HATS_SHOT" && ! -f "$HATS_SHOT" ]]; then
  echo "ERROR: Hats shot not found: $HATS_SHOT"
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
BUILD_ARGS=(--kick-times "$KICK_CSV" --hats-times "$HATS_CSV" --out "$PLACEMENTS_JSON")
if [[ -n "$KICK_SHOT" && -n "$HATS_SHOT" ]]; then
  BUILD_ARGS+=(--kick-shot "$KICK_SHOT" --hats-shot "$HATS_SHOT")
else
  SHOT="${ONE_SHOT:-${KICK_SHOT:-$HATS_SHOT}}"
  BUILD_ARGS+=(--one-shot "$SHOT")
fi
python3 src/build_drum_placements.py "${BUILD_ARGS[@]}"

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
# Export for Python heredoc
export STEMS_DIR PLACEMENTS_JSON MIX_CONFIG OUT_MP3
export ONE_SHOT KICK_SHOT HATS_SHOT
python3 << 'PYEOF'
import json
import subprocess
import os

stems_dir = os.environ["STEMS_DIR"].replace("\\", "/")
placements_path = os.environ["PLACEMENTS_JSON"]
drums_stem = stems_dir + "/drums.mp3"
one_shot = os.environ.get("ONE_SHOT", "").replace("\\", "/")
kick_shot = os.environ.get("KICK_SHOT", "").replace("\\", "/")
hats_shot = os.environ.get("HATS_SHOT", "").replace("\\", "/")

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

with open(placements_path) as f:
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

# Build drum_mask: per-track when placements has kick_events/hats_events; else legacy
if "kick_events" in placements and "hats_events" in placements and kick_shot and hats_shot:
  drum_mask = {
    "kick_one_shot_path": kick_shot,
    "kick_events": placements["kick_events"],
    "hats_one_shot_path": hats_shot,
    "hats_events": placements["hats_events"],
  }
else:
  drum_mask = {
    "one_shot_path": one_shot or kick_shot or hats_shot,
    "drum_events": placements["drum_events"],
  }

config = {
  "song_length_ms": song_len_ms,
  "sr": 48000,
  "instruments": instruments,
  "drum_mask": drum_mask,
}
with open(os.environ["MIX_CONFIG"], "w") as f:
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
