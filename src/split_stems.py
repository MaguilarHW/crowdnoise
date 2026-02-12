#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path
from importlib.util import find_spec


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    input_dir = project_root / "resources"
    output_dir = project_root / "output"
    model_name = "htdemucs_6s"

    if find_spec("demucs") is None:
        print("demucs not found in this Python environment.")
        print("Install with: pip install -U demucs")
        return 1
    if find_spec("torchcodec") is None:
        print("torchcodec not found in this Python environment.")
        print("Install with: pip install -U torchcodec")
        return 1

    if not input_dir.is_dir():
        print(f"Input folder not found: {input_dir}")
        print("Create it and add audio files (.wav/.mp3/.flac), then rerun.")
        return 1

    input_files = [
        p for p in input_dir.iterdir() if p.is_file() and p.name != ".gitkeep"
    ]
    if not input_files:
        print(f"No files found in {input_dir}")
        print("Add audio files and rerun.")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    model_output_dir = output_dir / model_name
    pending_files = []
    for input_file in input_files:
        stem_output_dir = model_output_dir / input_file.stem
        if stem_output_dir.is_dir() and any(stem_output_dir.iterdir()):
            print(f"Skipping already-split track: {input_file.name}")
            continue
        pending_files.append(input_file)

    if not pending_files:
        print("All tracks already split. Nothing to do.")
        return 0

    cmd = [
        sys.executable,
        "-m",
        "demucs",
        "-n",
        model_name,
        "--mp3",
        "-o",
        str(output_dir),
        *map(str, pending_files),
    ]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
