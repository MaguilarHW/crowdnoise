# Drums-only MVP: Timestamp-accurate mask pipeline

This document describes how to produce a recreation MP3 where the user's one-shot drum sample is overlaid at every detected kick and hats hit.

## Overview

- **Input**: Original song (Demucs stems), user-recorded drum sample (canonicalized via ingest), kick/hats hit timestamps
- **Output**: Mixed MP3 where drums = original Demucs drums **with user one-shot at every hit** (sample-accurate at 48 kHz)

## Pipeline steps

### 1. Scrape / download audio

Use `scrape_audio.py` (or equivalent) to obtain the original song audio.

### 2. Demucs split

```bash
python3 src/split_stems.py <audio_path>
# Output: output/htdemucs_6s/<song>/drums.mp3, bass.mp3, other.mp3, vocals.mp3
```

### 3. Isolate drums + export hit timestamps

```bash
python3 src/isolate_drums.py output/htdemucs_6s/<song>/drums.mp3 --export-hits --out-dir output/trackDecomp
# Output: output/trackDecomp/<song>/drum/kick_times.csv, hats_times.csv, kick.mp3, hats.mp3
```

### 4. Ingest user one-shot (if not already done)

```bash
./ingest_sample --input /path/to/user_recording.m4a
# Output: canonical/canonical.mp3 + JSON metadata
```

### 5. Build drum placements

```bash
python3 src/build_drum_placements.py \
  --kick-times output/trackDecomp/<song>/drum/kick_times.csv \
  --hats-times output/trackDecomp/<song>/drum/hats_times.csv \
  --one-shot canonical/canonical.mp3 \
  --out output/htdemucs_6s/<song>/drum_events.json
```

### 6. (Optional) Dry-run validation

```bash
python3 scripts/dry_run_drum_report.py \
  --kick-times output/trackDecomp/<song>/drum/kick_times.csv \
  --hats-times output/trackDecomp/<song>/drum/hats_times.csv \
  --song-length-ms <ms> \
  [--visualize --audio output/htdemucs_6s/<song>/drums.mp3]
```

### 7. Mix (one command)

```bash
./scripts/run_drums_mvp.sh \
  --stems-dir output/htdemucs_6s/<song> \
  --drum-dir output/trackDecomp/<song>/drum \
  --one-shot canonical/canonical.mp3 \
  --out recreation.mp3 \
  [--normalize]
```

Or build the mix config manually and run:

```bash
# Merge drum_events into a mix config JSON (see run_drums_mvp.sh for structure)
./bin/mix_json_cli mix_config.json out.mp3
```

### 8. (Optional) Loudness normalization

```bash
./scripts/normalize_loudness.sh out.mp3 out_normalized.mp3
```

## JSON schema (drum_mask)

The mix config supports an optional top-level `drum_mask` object:

```json
{
  "song_length_ms": 180000,
  "instruments": {
    "drums": {
      "active_path": "path/to/drums.mp3",
      "original_path": "path/to/drums.mp3"
    },
    ...
  },
  "drum_mask": {
    "one_shot_path": "path/to/canonical.mp3",
    "drum_events": [0.5, 1.2, 2.1, 2.8, ...]
  }
}
```

- `drum_events`: Array of hit times in seconds (from kick_times.csv + hats_times.csv, merged and sorted)
- `one_shot_path`: User one-shot to overlay at each hit
- When present, the mixer uses the original drums stem and **adds** the one-shot at each `drum_events` time (sample-accurate at 48 kHz)

## Verification

Use `visualize_hit_times.py` to confirm hits align with the waveform:

```bash
python3 src/visualize_hit_times.py \
  --kick-times output/trackDecomp/<song>/drum/kick_times.csv \
  --hats-times output/trackDecomp/<song>/drum/hats_times.csv \
  --audio output/htdemucs_6s/<song>/drums.mp3 \
  --out output/plots/hits.png
```

## Acceptance criteria (drums MVP)

- [x] User one-shot overlaid at **every** kick and hats hit
- [x] **Exact timestamps** from CSVs (sample-accurate 48 kHz)
- [x] Output MP3 is audible (loudness normalization available)
- [x] One command produces recreation from song + one-shot
