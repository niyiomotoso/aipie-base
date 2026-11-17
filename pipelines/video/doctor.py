"""Preflight. Fail here with a specific message, not halfway through a render.

Exit 0 = ready, 1 = something required is missing.
"""
import shutil
import subprocess
import sys

from . import config as C
from . import drive

NEEDED_FILTERS = ["xfade", "concat", "overlay", "zoompan", "loudnorm",
                  "silencedetect", "blackdetect", "freezedetect", "scale", "crop"]
NEEDED_ENCODERS = ["libx264", "aac"]


def _ok(label, good, detail=""):
    print(f"  {'OK  ' if good else 'FAIL'}  {label:<34} {detail}")
    return good


def main() -> int:
    print("=== video pipeline doctor")
    ready = True

    # binaries
    for b in ("ffmpeg", "ffprobe", "rclone"):
        ready &= _ok(b, shutil.which(b) is not None,
                     shutil.which(b) or "not on PATH")

    if shutil.which("ffmpeg"):
        filters = subprocess.run(["ffmpeg", "-hide_banner", "-filters"],
                                 capture_output=True, text=True).stdout
        missing = [f for f in NEEDED_FILTERS if f" {f} " not in filters]
        ready &= _ok("ffmpeg filters", not missing,
                     f"missing: {', '.join(missing)}" if missing else "all present")
        # drawtext/subtitles are expected to be ABSENT on the slim bottle; captions
        # are drawn by Pillow instead. Report, do not fail.
        has_text = any(f" {f} " in filters for f in ("drawtext", "subtitles"))
        print(f"  note  {'drawtext/subtitles present':<34} "
              f"{'yes - still using Pillow for per-word highlight' if has_text else 'no - Pillow path required'}")
        enc = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"],
                             capture_output=True, text=True).stdout
        miss_e = [e for e in NEEDED_ENCODERS if e not in enc]
        ready &= _ok("ffmpeg encoders", not miss_e,
                     f"missing: {', '.join(miss_e)}" if miss_e else "libx264, aac")

    # python deps
    try:
        import PIL
        from PIL import features
        ready &= _ok("Pillow + freetype", features.check("freetype2"),
                     f"Pillow {PIL.__version__}")
    except ImportError:
        ready &= _ok("Pillow", False, "pip install Pillow")
    try:
        import requests  # noqa: F401
        _ok("requests", True, "")
    except ImportError:
        ready &= _ok("requests", False, "pip install requests")

    # font
    from pathlib import Path
    ready &= _ok("caption font", Path(C.CAPTION_FONT).exists(), C.CAPTION_FONT)

    # drive
    try:
        remote = drive.have_remote()
    except Exception:
        remote = False
    ready &= _ok(f"rclone remote '{C.REMOTE}:'", remote,
                 "" if remote else "run: rclone config")
    if remote:
        try:
            print(f"  note  {'projects available':<34} "
                  f"{', '.join(drive.list_projects()) or '(none)'}")
        except Exception as e:
            print(f"  note  projects: could not list ({e})")

    # keys - names only, never values
    env = C.load_env()
    ready &= _ok("ELEVENLABS_API_KEY", bool(env.get("ELEVENLABS_API_KEY")),
                 "set" if env.get("ELEVENLABS_API_KEY") else "required for transcription")
    _ok("PIXABAY_API_KEY", bool(env.get("PIXABAY_API_KEY")),
        "set" if env.get("PIXABAY_API_KEY") else "optional, stock images only")

    # disk
    total, used, free = shutil.disk_usage(C.REPO)
    gb = free / 2**30
    ready &= _ok("free disk", gb >= 20, f"{gb:.0f} GiB")
    if 20 <= gb < 60:
        print("  note  disk is tight - a render plus intermediates wants ~20 GiB")

    print("\nready" if ready else "\nNOT READY - fix the FAIL lines above")
    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main())
