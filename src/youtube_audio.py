#!/usr/bin/env python3
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 2:
        query = input("Song title (and artist): ").strip()
        if not query:
            print("Usage: python3 src/youtube_audio.py \"Song Title Artist\"")
            return 1
    else:
        query = " ".join(sys.argv[1:]).strip()

    if shutil.which("yt-dlp") is None:
        print("yt-dlp not found in PATH. Install with: pip install -U yt-dlp")
        return 1

    if not query:
        print("Please provide a non-empty song title.")
        return 1

    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "resources"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_template = str(output_dir / "%(title)s.%(ext)s")
    cmd = [
        "yt-dlp",
        "ytsearch1:" + query,
        "-x",
        "--audio-format",
        "mp3",
        "-o",
        output_template,
    ]

    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
