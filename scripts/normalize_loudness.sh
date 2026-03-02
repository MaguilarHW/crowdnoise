#!/usr/bin/env bash
# Post-mix loudness normalization. Avoids quiet out.mp3.
#
# Uses ffmpeg loudnorm (EBU R128) or fallback to peak normalize.
# Usage:
#   ./scripts/normalize_loudness.sh input.mp3 output.mp3
#   ./scripts/normalize_loudness.sh input.mp3 output.mp3 --peak

set -e

INPUT="${1:?Missing input MP3}"
OUTPUT="${2:?Missing output MP3}"

if [[ ! -f "$INPUT" ]]; then
  echo "ERROR: Input file not found: $INPUT" >&2
  exit 1
fi

if ! command -v ffmpeg &>/dev/null; then
  echo "ERROR: ffmpeg not found. Install with: brew install ffmpeg" >&2
  exit 1
fi

# EBU R128 loudness normalization to ~-14 LUFS (audible playback level)
ffmpeg -y -hide_banner -loglevel error -i "$INPUT" \
  -af "loudnorm=I=-14:TP=-1:LRA=11" \
  "$OUTPUT"

echo "Normalized: $OUTPUT"
