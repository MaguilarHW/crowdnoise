#!/usr/bin/env python3
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    input_dir = project_root / "resources"
    output_dir = project_root / "output_stems"

    if shutil.which("demucs") is None:
        print("demucs not found in PATH. Install with: pip install -U demucs")
        return 1

    if not input_dir.is_dir():
        print(f"Input folder not found: {input_dir}")
        print("Create it and add audio files (.wav/.mp3/.flac), then rerun.")
        return 1

    input_files = [p for p in input_dir.iterdir() if p.is_file()]
    if not input_files:
        print(f"No files found in {input_dir}")
        print("Add audio files and rerun.")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = ["demucs", "-n", "htdemucs", "-o", str(output_dir), *map(str, input_files)]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
