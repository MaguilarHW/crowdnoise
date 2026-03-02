#!/usr/bin/env python3
"""
Dry-run report for drum placements: kick count, hats count, timestamp range vs song length.

Use before running the mixer to verify placement count and alignment.
Also supports invoking visualize_hit_times for visual verification.

Usage:
  python3 scripts/dry_run_drum_report.py --kick-times PATH --hats-times PATH [--song-length-ms N] [--visualize]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _load_times(csv_path: Path) -> list[float]:
    import csv
    times: list[float] = []
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "time_seconds" not in (reader.fieldnames or []):
            raise RuntimeError(f"CSV missing time_seconds column: {csv_path}")
        for row in reader:
            raw = (row.get("time_seconds") or "").strip()
            if raw:
                times.append(float(raw))
    return times


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run report for drum hit placements."
    )
    parser.add_argument("--kick-times", type=Path, required=True)
    parser.add_argument("--hats-times", type=Path, required=True)
    parser.add_argument(
        "--song-length-ms",
        type=float,
        default=0,
        help="Song length in ms (for range check)",
    )
    parser.add_argument(
        "--audio",
        type=Path,
        default=None,
        help="Reference audio for --visualize (e.g. drums stem)",
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Run visualize_hit_times.py to plot alignment",
    )
    args = parser.parse_args(argv)

    kick_times = _load_times(args.kick_times.resolve())
    hats_times = _load_times(args.hats_times.resolve())
    all_times = sorted(kick_times + hats_times)
    min_t = min(all_times) if all_times else 0.0
    max_t = max(all_times) if all_times else 0.0
    song_len_s = args.song_length_ms / 1000.0 if args.song_length_ms else 0.0

    print("Drum placement dry-run report")
    print("=" * 40)
    print(f"  Kick hits:     {len(kick_times)}")
    print(f"  Hats hits:     {len(hats_times)}")
    print(f"  Total placements: {len(all_times)}")
    print(f"  Timestamp range:  {min_t:.3f}s .. {max_t:.3f}s")
    if song_len_s > 0:
        ok = "OK" if max_t <= song_len_s else "WARN (max > song length)"
        print(f"  Song length:      {song_len_s:.3f}s  [{ok}]")
    print()

    if args.visualize:
        repo_root = Path(__file__).resolve().parents[1]
        viz_script = repo_root / "src" / "visualize_hit_times.py"
        if not viz_script.exists():
            print(f"ERROR: {viz_script} not found", file=sys.stderr)
            return 1
        if not args.audio:
            print("ERROR: --audio required when using --visualize (path to drums stem)", file=sys.stderr)
            return 1
        audio = args.audio.resolve()
        if not audio.exists():
            print(f"ERROR: Audio file not found: {audio}", file=sys.stderr)
            return 1
        cmd = [
            sys.executable,
            str(viz_script),
            "--kick-times", str(args.kick_times),
            "--hats-times", str(args.hats_times),
            "--audio", str(args.audio),
            "--no-show",
        ]
        subprocess.run(cmd, check=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
