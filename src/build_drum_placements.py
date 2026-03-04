#!/usr/bin/env python3
"""
Build drum placement segments from kick_times.csv + hats_times.csv.

Reads hit timestamps, optionally gets one-shot duration from ingest JSON or by decoding,
and outputs drum events. With --kick-shot and --hats-shot: outputs kick_events, hats_events
with separate one-shot paths. With --one-shot: outputs legacy drum_events + one_shot_path.

Usage:
  python3 src/build_drum_placements.py --kick-times PATH --hats-times PATH --one-shot PATH [--ingest-json PATH] --out EVENTS.json
  python3 src/build_drum_placements.py --kick-times PATH --hats-times PATH --kick-shot PATH --hats-shot PATH --out EVENTS.json
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
        default=None,
        help="Path to user one-shot (single for both kick+hats). Required unless --kick-shot and --hats-shot provided.",
    )
    parser.add_argument(
        "--kick-shot",
        type=Path,
        default=None,
        help="Path to kick one-shot (use with --hats-shot for per-track drum mask)",
    )
    parser.add_argument(
        "--hats-shot",
        type=Path,
        default=None,
        help="Path to hats one-shot (use with --kick-shot for per-track drum mask)",
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

    has_both = args.kick_shot is not None and args.hats_shot is not None
    has_one = args.one_shot is not None
    if not has_both and not has_one:
        parser.error("Provide --one-shot, or both --kick-shot and --hats-shot")

    kick_times = _load_times_csv(args.kick_times.resolve())
    hats_times = _load_times_csv(args.hats_times.resolve())

    # Merge and sort; keep type for report
    events: list[float] = sorted(kick_times + hats_times)
    kick_set = set(kick_times)
    hats_set = set(hats_times)

    if has_both:
        # Per-track mode: output kick_events, kick_one_shot_path, hats_events, hats_one_shot_path
        kick_path = str(args.kick_shot.resolve())
        hats_path = str(args.hats_shot.resolve())
        out_obj: dict = {
            "kick_events": kick_times,
            "kick_one_shot_path": kick_path,
            "hats_events": hats_times,
            "hats_one_shot_path": hats_path,
            "kick_count": len(kick_times),
            "hats_count": len(hats_times),
        }
    else:
        # Legacy mode: drum_events + one_shot_path
        one_shot_path = args.one_shot.resolve()
        one_shot_duration_s = 0.0
        if args.ingest_json and args.ingest_json.exists():
            one_shot_duration_s = _get_duration_from_ingest_json(args.ingest_json.resolve()) or 0.0
        if one_shot_duration_s <= 0:
            one_shot_duration_s = _get_one_shot_duration_seconds(one_shot_path)

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

        out_obj = {
            "drum_events": events,
            "one_shot_path": str(one_shot_path),
            "one_shot_duration_seconds": one_shot_duration_s,
            "placement_count": len(events),
            "kick_count": len(kick_times),
            "hats_count": len(hats_times),
        }
        segments = []
        for t in events:
            start_ms = t * 1000.0
            end_ms = (t + one_shot_duration_s) * 1000.0
            segments.append({"start_ms": start_ms, "end_ms": end_ms})
        out_obj["segments"] = segments

    if args.dry_run and has_both:
        min_t = min(events) if events else 0.0
        max_t = max(events) if events else 0.0
        print(
            f"Dry-run report:\n"
            f"  kick hits: {len(kick_times)}\n"
            f"  hats hits: {len(hats_times)}\n"
            f"  total placements: {len(events)}\n"
            f"  timestamp range: {min_t:.3f}s .. {max_t:.3f}s\n"
            f"  per-track mode: kick_shot + hats_shot"
        )
        return 0

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
