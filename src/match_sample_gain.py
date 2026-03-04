#!/usr/bin/env python3
"""
Compute gain so user-recorded sample matches volume of reference track at hit times.

Usage:
  python3 src/match_sample_gain.py --reference MVP\ demo/drum/kick.mp3 \\
    --sample MVP\ demo/my_kick.mp3 --times MVP\ demo/drum/kick_times.csv

Prints the gain multiplier to stdout (for --gain in repeat_sample_at_times_cli).
Accepts MP3 or WAV for reference and sample; reference is the instrument being replaced.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import numpy as np


def _load_audio(path: Path) -> tuple[np.ndarray, int]:
    try:
        import librosa
    except ImportError as e:
        raise RuntimeError("librosa required: pip install librosa") from e
    y, sr = librosa.load(str(path), sr=None, mono=True)
    return y.astype(np.float32), int(sr)


def _rms(x: np.ndarray) -> float:
    if x.size == 0:
        return 1e-10  # avoid division by zero
    return float(np.sqrt(np.mean(x.astype(np.float64) ** 2)))


def _load_times(path: Path) -> list[float]:
    times: list[float] = []
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        if "time_seconds" not in (reader.fieldnames or []):
            raise ValueError("CSV must have 'time_seconds' column")
        for row in reader:
            t = row.get("time_seconds", "").strip()
            if not t:
                continue
            try:
                times.append(float(t))
            except ValueError:
                continue
    return sorted(times)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compute gain so user sample matches reference volume at hit times."
    )
    parser.add_argument("--reference", type=Path, required=True, help="Reference track (kick.mp3 or hats.mp3) — the instrument being replaced.")
    parser.add_argument("--sample", type=Path, required=True, help="User-recorded sample (mp3/wav).")
    parser.add_argument("--times", type=Path, required=True, help="Hit times CSV (time_seconds).")
    parser.add_argument(
        "--min-gain",
        type=float,
        default=0.1,
        help="Clamp gain to at least this (default 0.1).",
    )
    parser.add_argument(
        "--max-gain",
        type=float,
        default=10.0,
        help="Clamp gain to at most this (default 10.0).",
    )
    parser.add_argument(
        "--window-ms",
        type=float,
        default=500.0,
        help="Window around each hit to measure reference RMS (default 500ms).",
    )
    args = parser.parse_args()

    ref_path = args.reference.resolve()
    sample_path = args.sample.resolve()
    times_path = args.times.resolve()

    if not ref_path.exists():
        print(f"ERROR: Reference not found: {ref_path}", file=sys.stderr)
        return 1
    if not sample_path.exists():
        print(f"ERROR: Sample not found: {sample_path}", file=sys.stderr)
        return 1
    if not times_path.exists():
        print(f"ERROR: Times CSV not found: {times_path}", file=sys.stderr)
        return 1

    ref_y, ref_sr = _load_audio(ref_path)
    sample_y, sample_sr = _load_audio(sample_path)
    times = _load_times(times_path)

    if not times:
        print("ERROR: No timestamps in CSV.", file=sys.stderr)
        return 1

    sample_rms = _rms(sample_y)
    if sample_rms < 1e-10:
        print("ERROR: Sample is silent.", file=sys.stderr)
        return 1

    window_samples = int(round((args.window_ms / 1000.0) * ref_sr))
    window_samples = max(1, min(window_samples, ref_y.shape[0] // 2))

    ref_rms_list: list[float] = []
    for t in times:
        center = int(round(t * ref_sr))
        start = max(0, center - window_samples // 2)
        end = min(ref_y.shape[0], start + window_samples)
        if end <= start:
            continue
        chunk = ref_y[start:end]
        r = _rms(chunk)
        if r > 1e-10:
            ref_rms_list.append(r)

    if not ref_rms_list:
        print("1.0", end="")
        return 0

    ref_avg_rms = float(np.median(ref_rms_list))  # median to ignore outliers
    gain = ref_avg_rms / sample_rms
    gain = max(args.min_gain, min(args.max_gain, gain))
    print(f"{gain:.4f}", end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
