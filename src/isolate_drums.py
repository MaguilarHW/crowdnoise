#!/usr/bin/env python3.10
"""
Isolate "low" and "high" percussion from a drum/percussion track using filters.

Default repo layout (if you pass a file from `resources/`):
  - input:  resources/<file>.mp3
  - output: output/trackDecomp/<file>_kick.mp3, output/trackDecomp/<file>_hats.mp3

What it does:
  - Loads the MP3 (mono) with librosa
  - "Kick-like" stem: band-pass around ~40–160 Hz
  - "Hat/cymbal-like" stem: high-pass above ~7 kHz
  - Optional simple transient gate (envelope threshold) to reduce bleed

Notes:
  - MP3 decoding may require ffmpeg on some systems (e.g. `brew install ffmpeg`).
  - MP3 encoding requires ffmpeg as well.
  - Filtering won't perfectly isolate drums (spectral overlap), but it’s a solid baseline.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np


def _require_python310() -> None:
    major, minor = sys.version_info[:2]
    if (major, minor) != (3, 10):
        raise RuntimeError(
            f"This script must be run with Python 3.10 (you are running {major}.{minor}).\n"
            "Run it with:\n"
            "  python3.10 src/isolate_drums.py path/to/audio.mp3\n"
        )


def _repo_root() -> Path:
    # src/isolate_drums.py -> repo root
    return Path(__file__).resolve().parents[1]


def _load_mono_audio(audio_path: Path) -> tuple[np.ndarray, int]:
    try:
        import librosa  # imported lazily for friendlier CLI errors
    except Exception as e:  # noqa: BLE001 - CLI tool
        raise RuntimeError(
            "librosa is not installed (or failed to import).\n"
            "Install dependencies (basic-pitch pulls in librosa), e.g.:\n"
            "  pip install basic-pitch\n"
        ) from e

    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    if y.size == 0:
        raise RuntimeError(f"Loaded empty audio: {audio_path}")
    return y.astype(np.float32, copy=False), int(sr)


def _butter_sos_filter(
    x: np.ndarray,
    sr: int,
    *,
    kind: str,
    f1_hz: float,
    f2_hz: float | None = None,
    order: int = 6,
) -> np.ndarray:
    """
    Butterworth IIR filter applied with zero-phase filtering (preserves transients).
    """
    try:
        from scipy.signal import butter, sosfiltfilt  # type: ignore
    except Exception as e:  # noqa: BLE001 - CLI tool
        raise RuntimeError(
            "scipy is not installed (or failed to import).\n"
            "Install it with:\n"
            "  pip install scipy\n"
        ) from e

    nyq = 0.5 * sr
    if nyq <= 0:
        raise ValueError("Invalid sample rate.")

    if kind == "lowpass":
        wn = f1_hz / nyq
        sos = butter(order, wn, btype="lowpass", output="sos")
    elif kind == "highpass":
        wn = f1_hz / nyq
        sos = butter(order, wn, btype="highpass", output="sos")
    elif kind == "bandpass":
        if f2_hz is None:
            raise ValueError("bandpass requires f2_hz.")
        wn = [f1_hz / nyq, f2_hz / nyq]
        sos = butter(order, wn, btype="bandpass", output="sos")
    else:
        raise ValueError("kind must be: lowpass | highpass | bandpass")

    y = sosfiltfilt(sos, x)
    return y.astype(np.float32, copy=False)


def _envelope_follower(
    x: np.ndarray,
    sr: int,
    *,
    attack_ms: float = 5.0,
    release_ms: float = 80.0,
) -> np.ndarray:
    """
    Simple attack/release envelope follower on |x|.
    """
    if sr <= 0:
        raise ValueError("Invalid sample rate.")

    attack = float(np.exp(-1.0 / (sr * (attack_ms / 1000.0))))
    release = float(np.exp(-1.0 / (sr * (release_ms / 1000.0))))

    env = np.zeros_like(x, dtype=np.float32)
    prev = 0.0
    for i in range(x.shape[0]):
        rect = float(abs(x[i]))
        if rect > prev:
            prev = attack * prev + (1.0 - attack) * rect
        else:
            prev = release * prev + (1.0 - release) * rect
        env[i] = prev
    return env


def _soft_gate_from_envelope(
    x: np.ndarray,
    env: np.ndarray,
    *,
    thresh_db: float,
    smooth_ms: float,
    sr: int,
) -> np.ndarray:
    """
    Create a smooth gate mask from an envelope, then apply it.
    """
    env_db = 20.0 * np.log10(np.maximum(env, 1e-8))
    mask = (env_db >= thresh_db).astype(np.float32)

    # Smooth mask to reduce clicks.
    if smooth_ms > 0:
        win = int(max(1, round((smooth_ms / 1000.0) * sr)))
        kernel = np.ones(win, dtype=np.float32) / float(win)
        mask = np.convolve(mask, kernel, mode="same")

    return (x * mask).astype(np.float32, copy=False)


def _normalize_if_needed(y: np.ndarray) -> np.ndarray:
    peak = float(np.max(np.abs(y))) if y.size else 0.0
    if peak <= 1.0 or peak == 0.0:
        return y
    return (y / peak).astype(np.float32, copy=False)


def isolate_drums(
    audio_path: Path,
    *,
    kick_low_hz: float = 40.0,
    kick_high_hz: float = 160.0,
    hats_highpass_hz: float = 7000.0,
    filter_order: int = 6,
    gate: bool = True,
    kick_gate_db: float = -35.0,
    hats_gate_db: float = -40.0,
    gate_attack_ms: float = 5.0,
    gate_release_ms: float = 80.0,
    gate_smooth_ms: float = 10.0,
) -> tuple[np.ndarray, np.ndarray, int]:
    y, sr = _load_mono_audio(audio_path)

    kick = _butter_sos_filter(
        y,
        sr,
        kind="bandpass",
        f1_hz=kick_low_hz,
        f2_hz=kick_high_hz,
        order=filter_order,
    )
    hats = _butter_sos_filter(
        y,
        sr,
        kind="highpass",
        f1_hz=hats_highpass_hz,
        order=filter_order,
    )

    if gate:
        kick_env = _envelope_follower(kick, sr, attack_ms=gate_attack_ms, release_ms=gate_release_ms)
        hats_env = _envelope_follower(hats, sr, attack_ms=gate_attack_ms, release_ms=gate_release_ms)
        kick = _soft_gate_from_envelope(
            kick,
            kick_env,
            thresh_db=kick_gate_db,
            smooth_ms=gate_smooth_ms,
            sr=sr,
        )
        hats = _soft_gate_from_envelope(
            hats,
            hats_env,
            thresh_db=hats_gate_db,
            smooth_ms=gate_smooth_ms,
            sr=sr,
        )

    return kick, hats, sr


def _write_wav(path: Path, y: np.ndarray, sr: int) -> None:
    try:
        import soundfile as sf  # type: ignore
    except Exception as e:  # noqa: BLE001 - CLI tool
        raise RuntimeError(
            "soundfile is not installed (or failed to import).\n"
            "Install it with:\n"
            "  pip install soundfile\n"
        ) from e

    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), _normalize_if_needed(y), sr, subtype="FLOAT")


def _write_mp3(path: Path, y: np.ndarray, sr: int, *, bitrate: str = "192k") -> None:
    """
    Write an MP3 by writing a temporary WAV and converting with ffmpeg.
    """
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError(
            "ffmpeg was not found on your PATH. MP3 encoding requires ffmpeg.\n"
            "Install it with:\n"
            "  brew install ffmpeg\n"
        )

    path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        prefix=f".{path.stem}_",
        suffix=".wav",
        dir=str(path.parent),
        delete=False,
    ) as tmp:
        tmp_wav = Path(tmp.name)

    try:
        _write_wav(tmp_wav, y, sr)
        cmd = [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(tmp_wav),
            "-vn",
            "-codec:a",
            "libmp3lame",
            "-b:a",
            bitrate,
            str(path),
        ]
        subprocess.run(cmd, check=True)
    finally:
        try:
            tmp_wav.unlink(missing_ok=True)
        except Exception:
            pass


def main(argv: list[str] | None = None) -> int:
    _require_python310()
    root = _repo_root()

    parser = argparse.ArgumentParser(
        description="Isolate low/high percussion from a drum/percussion track using filters."
    )
    parser.add_argument(
        "audio",
        type=Path,
        help="Path to input drum/percussion audio (mp3/wav/etc).",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=root / "output" / "trackDecomp",
        help="Directory to write output MP3 stems.",
    )

    # Filter parameters
    parser.add_argument("--kick-low-hz", type=float, default=40.0)
    parser.add_argument("--kick-high-hz", type=float, default=160.0)
    parser.add_argument("--hats-highpass-hz", type=float, default=7000.0)
    parser.add_argument("--order", type=int, default=6, help="Butterworth filter order (e.g. 4–8).")

    # Gate parameters
    parser.add_argument("--no-gate", action="store_true", help="Disable transient gating.")
    parser.add_argument("--kick-gate-db", type=float, default=-35.0)
    parser.add_argument("--hats-gate-db", type=float, default=-40.0)
    parser.add_argument("--gate-attack-ms", type=float, default=5.0)
    parser.add_argument("--gate-release-ms", type=float, default=80.0)
    parser.add_argument("--gate-smooth-ms", type=float, default=10.0)

    # MP3 output
    parser.add_argument(
        "--mp3-bitrate",
        type=str,
        default="192k",
        help="MP3 bitrate to pass to ffmpeg (e.g. 128k, 192k, 320k).",
    )

    args = parser.parse_args(argv)

    audio_path: Path = args.audio.resolve()
    if not audio_path.exists():
        print(f"ERROR: Audio file not found: {audio_path}", file=sys.stderr)
        return 1

    try:
        kick, hats, sr = isolate_drums(
            audio_path,
            kick_low_hz=args.kick_low_hz,
            kick_high_hz=args.kick_high_hz,
            hats_highpass_hz=args.hats_highpass_hz,
            filter_order=args.order,
            gate=not args.no_gate,
            kick_gate_db=args.kick_gate_db,
            hats_gate_db=args.hats_gate_db,
            gate_attack_ms=args.gate_attack_ms,
            gate_release_ms=args.gate_release_ms,
            gate_smooth_ms=args.gate_smooth_ms,
        )
    except Exception as e:  # noqa: BLE001 - CLI script
        msg = str(e).strip() or e.__class__.__name__
        print(f"ERROR: {msg}", file=sys.stderr)
        return 1

    out_dir: Path = args.out_dir.resolve()
    stem = audio_path.stem
    kick_path = out_dir / f"{stem}_kick.mp3"
    hats_path = out_dir / f"{stem}_hats.mp3"

    try:
        _write_mp3(kick_path, kick, sr, bitrate=args.mp3_bitrate)
        _write_mp3(hats_path, hats, sr, bitrate=args.mp3_bitrate)
    except Exception as e:  # noqa: BLE001 - CLI script
        msg = str(e).strip() or e.__class__.__name__
        print(f"ERROR: {msg}", file=sys.stderr)
        return 1

    print(f"Wrote: {kick_path}")
    print(f"Wrote: {hats_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

