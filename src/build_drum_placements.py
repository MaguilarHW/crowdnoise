#!/usr/bin/env python3
"""
Build drum placement segments from kick_times.csv + hats_times.csv.

Reads hit timestamps, optionally gets one-shot duration from ingest JSON or by decoding,
and outputs a merged drum_events list (time_seconds) plus optional placement segments (start_ms, end_ms).

Usage:
  python3 src/build_drum_placements.py --kick-times PATH --hats-times PATH --one-shot PATH [--ingest-json PATH] --out EVENTS.json
  python3 src/build_drum_placements.py --kick-times PATH --hats-times PATH --one-shot PATH --out -  # stdout
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def _load_times_csv(path: Path) -> list[float]:
    """Load time_seconds column from CSV."""
    times: list[float] = []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "time_seconds" not in (reader.fieldnames or []):
            raise RuntimeError(
                f"CSV missing 'time_seconds' column: {path}\n"
                "Expected columns: index,time_seconds"
            )
        for row in reader:
            raw = (row.get("time_seconds") or "").strip()
            if not raw:
                continue
            times.append(float(raw))
    return times


def _get_one_shot_duration_seconds(path: Path) -> float:
    """Get duration of one-shot file in seconds (via librosa)."""
    try:
        import librosa  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "librosa required to get one-shot duration.\n"
            "Install: pip install librosa"
        ) from e
    y, sr = librosa.load(str(path), sr=None, mono=True)
    if y.size == 0:
        return 0.0
    return float(len(y)) / float(sr)


def _get_duration_from_ingest_json(ingest_path: Path) -> float | None:
    """Get duration from ingest JSON if present (canonical_duration_seconds or similar)."""
    data = json.loads(ingest_path.read_text(encoding="utf-8"))
    val = data.get("canonical_duration_seconds") or data.get("duration_seconds")
    return float(val) if val is not None else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build drum placement events from kick_times.csv + hats_times.csv."
    )
    parser.add_argument("--kick-times", type=Path, required=True, help="Path to kick_times.csv")
    parser.add_argument("--hats-times", type=Path, required=True, help="Path to hats_times.csv")
    parser.add_argument(
        "--one-shot",
        type=Path,
        required=True,
        help="Path to user one-shot (for duration; also passed to mixer)",
    )
    parser.add_argument(
        "--ingest-json",
        type=Path,
        default=None,
        help="Optional ingest output JSON for canonical duration",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="-",
        help="Output path for drum_events JSON (default: stdout)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print report only (kick count, hats count, timestamp range) and exit",
    )
    args = parser.parse_args(argv)

    kick_times = _load_times_csv(args.kick_times.resolve())
    hats_times = _load_times_csv(args.hats_times.resolve())

    # Merge and sort; keep type for report
    events: list[float] = sorted(kick_times + hats_times)
    kick_set = set(kick_times)
    hats_set = set(hats_times)

    # Duration for placement segments (start_ms, end_ms)
    one_shot_duration_s = 0.0
    if args.ingest_json and args.ingest_json.exists():
        one_shot_duration_s = _get_duration_from_ingest_json(args.ingest_json.resolve()) or 0.0
    if one_shot_duration_s <= 0:
        one_shot_duration_s = _get_one_shot_duration_seconds(args.one_shot.resolve())

    if args.dry_run:
        min_t = min(events) if events else 0.0
        max_t = max(events) if events else 0.0
        print(
            f"Dry-run report:\n"
            f"  kick hits: {len(kick_times)}\n"
            f"  hats hits: {len(hats_times)}\n"
            f"  total placements: {len(events)}\n"
            f"  timestamp range: {min_t:.3f}s .. {max_t:.3f}s\n"
            f"  one-shot duration: {one_shot_duration_s:.3f}s"
        )
        return 0

    out_obj: dict = {
        "drum_events": events,
        "one_shot_path": str(args.one_shot.resolve()),
        "one_shot_duration_seconds": one_shot_duration_s,
        "placement_count": len(events),
        "kick_count": len(kick_times),
        "hats_count": len(hats_times),
    }

    # Optional: add segments as start_ms, end_ms for compatibility
    segments = []
    for t in events:
        start_ms = t * 1000.0
        end_ms = (t + one_shot_duration_s) * 1000.0
        segments.append({"start_ms": start_ms, "end_ms": end_ms})
    out_obj["segments"] = segments

    out_json = json.dumps(out_obj, indent=2)

    if args.out == "-":
        print(out_json)
    else:
        out_path = Path(args.out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(out_json, encoding="utf-8")
        print(f"Wrote: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
