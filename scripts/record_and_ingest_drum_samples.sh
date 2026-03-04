#!/usr/bin/env bash
# Record kick+hats via ffmpeg or accept --kick-file/--hats-file, run ingest_sample,
# output recorded_samples/ingest_result.json with kick_canonical, hats_canonical.
# Use --beep-only to generate sine beeps instead of recording.
#
# Usage:
#   ./scripts/record_and_ingest_drum_samples.sh [--kick-file PATH] [--hats-file PATH]
#   ./scripts/record_and_ingest_drum_samples.sh --beep-only

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

INGEST_BIN="$REPO_ROOT/src/ingest_sample"
STORAGE_ROOT="$REPO_ROOT/recorded_samples/storage"
OUT_JSON="$REPO_ROOT/recorded_samples/ingest_result.json"
RECORD_DURATION=5

KICK_FILE=""
HATS_FILE=""
BEEP_ONLY=false

usage() {
  echo "Usage: $0 [--kick-file PATH] [--hats-file PATH] [--beep-only]"
  echo "  --kick-file   Pre-recorded kick sample (skip kick recording)"
  echo "  --hats-file   Pre-recorded hats sample (skip hats recording)"
  echo "  --beep-only   Generate sine beeps instead of recording (no mic)"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case $1 in
    --kick-file)  KICK_FILE="$2"; shift 2 ;;
    --hats-file)  HATS_FILE="$2"; shift 2 ;;
    --beep-only)  BEEP_ONLY=true; shift 1 ;;
    -h|--help)    usage ;;
    *)            echo "Unknown option: $1"; usage ;;
  esac
done

if [[ ! -x "$INGEST_BIN" ]]; then
  echo "ERROR: ingest_sample not found or not executable: $INGEST_BIN"
  exit 1
fi

if ! command -v ffmpeg &>/dev/null; then
  echo "ERROR: ffmpeg required. Install with: brew install ffmpeg"
  exit 1
fi

mkdir -p "$STORAGE_ROOT"
mkdir -p "$(dirname "$OUT_JSON")"

# Trim WAV to short drum hit: find onset, keep (onset-0.05s) to (onset+0.35s), max 0.4s
_trim_drum_hit() {
  local wav_path="$1"
  local threshold="${2:-800}"
  python3 - "$wav_path" "$threshold" << 'PYTRIM'
import wave
import struct
import sys

path = sys.argv[1]
threshold = int(sys.argv[2])

with wave.open(path, "rb") as w:
  nch = w.getnchannels()
  sr = w.getframerate()
  nframes = w.getnframes()
  sampwidth = w.getsampwidth()
  frames = w.readframes(nframes)

# Unpack 16-bit samples
nsamples = len(frames) // (sampwidth * nch)
vals = []
for i in range(nsamples):
  off = i * sampwidth * nch
  v = struct.unpack_from("<h", frames, off)[0]
  vals.append(abs(v))

# Find first sample above threshold
onset_idx = None
for i, v in enumerate(vals):
  if v > threshold:
    onset_idx = i
    break

if onset_idx is None:
  sys.exit(0)  # No onset found, leave file as-is

onset_time = onset_idx / (sr * nch)
pre_s = 0.05
post_s = 0.35
start_time = max(0, onset_time - pre_s)
end_time = min(onset_time + post_s, nframes / (sr * nch))
if end_time - start_time > 0.4:
  end_time = start_time + 0.4

start_idx = int(start_time * sr * nch)
end_idx = int(end_time * sr * nch)
start_idx = max(0, min(start_idx, nsamples - 1))
end_idx = max(start_idx, min(end_idx, nsamples))

trimmed = frames[start_idx * sampwidth * nch : end_idx * sampwidth * nch]

with wave.open(path, "wb") as w:
  w.setnchannels(nch)
  w.setsampwidth(sampwidth)
  w.setframerate(sr)
  w.writeframes(trimmed)
PYTRIM
}

_record_or_beep() {
  local kind="$1"   # kick or hats
  local out_path="$2"
  local freq="${3:-60}"   # default kick ~60Hz, hats ~8000

  if $BEEP_ONLY; then
    echo "Generating $kind beep (${freq}Hz, 0.4s)..."
    ffmpeg -y -hide_banner -loglevel error \
      -f lavfi -i "sine=frequency=${freq}:duration=0.4" \
      -ac 1 -ar 48000 "$out_path"
  else
    echo "Recording $kind for ${RECORD_DURATION}s... (use default mic)"
    capture_err=$(mktemp)
    (
      ffmpeg -y -hide_banner -loglevel warning \
        -f avfoundation -i ":0" -t "$RECORD_DURATION" \
        -ac 1 -ar 48000 "$out_path" 2>/dev/null || \
      ffmpeg -y -hide_banner -loglevel warning \
        -f sndio -i default -t "$RECORD_DURATION" \
        -ac 1 -ar 48000 "$out_path" 2>/dev/null || \
      { echo "ERROR: No suitable capture device. Try --beep-only for testing."; echo 1 > "$capture_err"; exit 1; }
    ) &
    local ffmpeg_pid=$!
    local elapsed=0
    local bar_width=20
    while kill -0 "$ffmpeg_pid" 2>/dev/null; do
      sleep 0.2
      elapsed=$(echo "$elapsed + 0.2" | bc)
      if (( $(echo "$elapsed >= $RECORD_DURATION" | bc -l) )); then
        elapsed=$RECORD_DURATION
      fi
      local pct=$(echo "scale=0; $elapsed * 100 / $RECORD_DURATION" | bc)
      local filled=$(echo "scale=0; $elapsed * $bar_width / $RECORD_DURATION" | bc)
      filled=${filled:-0}
      [[ "$filled" -gt "$bar_width" ]] && filled=$bar_width
      local empty=$((bar_width - filled))
      [[ $empty -lt 0 ]] && empty=0
      local bar_filled="" bar_empty=""
      [[ $filled -gt 0 ]] && bar_filled=$(printf "#%.0s" $(seq 1 $filled))
      [[ $empty -gt 0 ]] && bar_empty=$(printf '\055%.0s' $(seq 1 $empty))
      printf "\r[%s%s] %d%% (%gs/%gs) " "$bar_filled" "$bar_empty" "$pct" "$elapsed" "$RECORD_DURATION"
    done
    printf "\r"
    wait "$ffmpeg_pid" || true
    if [[ -f "$capture_err" ]]; then
      rm -f "$capture_err"
      exit 1
    fi
    echo "Recording $kind done."
    _trim_drum_hit "$out_path"
  fi
}

_run_ingest() {
  local input="$1"
  local sample_id="$2"
  local json
  json="$("$INGEST_BIN" --input "$input" --storage-root "$STORAGE_ROOT" --sample-id "$sample_id" 2>/dev/null)"
  if [[ $? -ne 0 ]]; then
    echo "ERROR: ingest_sample failed for $sample_id"
    exit 1
  fi
  python3 -c "import json; d=json.loads('''$json'''.replace(\"'''\", \"'\")); print(d.get('canonical_mp3',{}).get('path',''))"
}

# Resolve kick source
KICK_INPUT=""
if [[ -n "$KICK_FILE" ]]; then
  if [[ ! -f "$KICK_FILE" ]]; then
    echo "ERROR: Kick file not found: $KICK_FILE"
    exit 1
  fi
  KICK_INPUT="$KICK_FILE"
else
  KICK_RAW="$STORAGE_ROOT/raw_kick.wav"
  _record_or_beep "kick" "$KICK_RAW" 60
  KICK_INPUT="$KICK_RAW"
fi

# Resolve hats source
HATS_INPUT=""
if [[ -n "$HATS_FILE" ]]; then
  if [[ ! -f "$HATS_FILE" ]]; then
    echo "ERROR: Hats file not found: $HATS_FILE"
    exit 1
  fi
  HATS_INPUT="$HATS_FILE"
else
  HATS_RAW="$STORAGE_ROOT/raw_hats.wav"
  _record_or_beep "hats" "$HATS_RAW" 8000
  HATS_INPUT="$HATS_RAW"
fi

# Ingest both
echo "Ingesting kick..."
KICK_CANONICAL="$(_run_ingest "$KICK_INPUT" "kick_canonical")"
echo "Ingesting hats..."
HATS_CANONICAL="$(_run_ingest "$HATS_INPUT" "hats_canonical")"

if [[ -z "$KICK_CANONICAL" || -z "$HATS_CANONICAL" ]]; then
  echo "ERROR: Ingest failed to produce canonical paths"
  exit 1
fi

# Write ingest_result.json (use abs paths)
export OUT_JSON KICK_CANONICAL HATS_CANONICAL
python3 << 'PYEOF'
import json
import os

out = {
  "kick_canonical": os.path.abspath(os.environ["KICK_CANONICAL"]),
  "hats_canonical": os.path.abspath(os.environ["HATS_CANONICAL"]),
}
with open(os.environ["OUT_JSON"], "w") as f:
  json.dump(out, f, indent=2)
PYEOF

echo "Done: $OUT_JSON"
echo "  kick_canonical: $KICK_CANONICAL"
echo "  hats_canonical: $HATS_CANONICAL"
