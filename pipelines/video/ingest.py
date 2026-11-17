"""Phase 1: pull footage, probe it safely, extract audio, transcribe.

Produces facts, no opinions. Writes data/video/<project>/raw_transcript.json.
"""
import hashlib
import json
import pathlib
import subprocess
import sys
import time

from . import config as C
from . import drive

VIDEO_EXT = {".mov", ".mp4", ".m4v", ".mkv", ".avi"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".heic", ".webp"}


def sniff(path: pathlib.Path) -> str:
    """Identify by magic bytes, never by extension - a downloaded file may lie."""
    head = path.open("rb").read(16)
    if head[:4] == b"\x1aE\xdf\xa3":
        return "matroska"
    if head[4:8] == b"ftyp":
        return "mov"
    if head[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    return "unknown"


def safe_input(path: pathlib.Path) -> list:
    """ffmpeg args that stop a crafted file reading other files or URLs."""
    kind = sniff(path)
    args = ["-protocol_whitelist", "file", "-enable_drefs", "0"]
    if kind in ("matroska", "mov"):
        args += ["-f", "matroska" if kind == "matroska" else "mov"]
    return args + ["-i", f"file:{path}"]


def probe(path: pathlib.Path) -> dict:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=index,codec_type,codec_name,width,height,r_frame_rate,channels,sample_rate",
         "-show_entries", "format=duration,size", "-of", "json",
         "-protocol_whitelist", "file", f"file:{path}"],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffprobe failed on {path.name}: {r.stderr.strip()[:200]}")
    return json.loads(r.stdout)


def extract_audio(src: pathlib.Path, dst: pathlib.Path) -> pathlib.Path:
    cmd = ["ffmpeg", "-v", "error", "-y"] + safe_input(src) + [
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "libmp3lame", "-b:a", "48k", str(dst)]
    if subprocess.run(cmd).returncode != 0:
        raise RuntimeError("audio extraction failed")
    return dst


def transcribe(audio: pathlib.Path, env: dict, tries: int = 4) -> dict:
    """Whole track in ONE request - chunking splits words across boundaries."""
    import requests
    key = env.get("ELEVENLABS_API_KEY")
    if not key:
        raise SystemExit("ELEVENLABS_API_KEY is not set (see .env)")
    print(f"transcribing {audio.name} ({audio.stat().st_size/1e6:.1f} MB)...")
    for n in range(tries):
        with audio.open("rb") as fh:
            r = requests.post(
                f"{C.ELEVEN_BASE}/v1/speech-to-text",
                headers={"xi-api-key": key},
                data={"model_id": C.STT_MODEL, "timestamps_granularity": "word",
                      "tag_audio_events": "true", "diarize": "false"},
                files={"file": (audio.name, fh, "audio/mpeg")}, timeout=900)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 500, 502, 503) and n < tries - 1:
            wait = 2 * (n + 1)
            print(f"  HTTP {r.status_code}, retrying in {wait}s")
            time.sleep(wait)
            continue
        raise RuntimeError(C.redact(f"speech-to-text refused (HTTP {r.status_code}): "
                                    f"{r.text[:400]}", env))
    raise RuntimeError("speech-to-text: no answer")


def main(project: str) -> int:
    work = C.project_dir(project)
    src_dir = work / "source"
    src_dir.mkdir(exist_ok=True)
    drive.ensure_mirror(project)

    files = drive.pull(project, src_dir)
    videos = [f for f in files if f.suffix.lower() in VIDEO_EXT]
    images = [f for f in files if f.suffix.lower() in IMAGE_EXT]
    if not videos:
        raise SystemExit(f"no video files in Videos Unedited/{project}")
    if len(videos) > 1:
        print(f"note: {len(videos)} video files; this skill expects one narration take "
              f"file. Using {videos[0].name}")
    src = videos[0]
    print(f"\nimages provided by Niyi: {len(images)}"
          + (f" ({', '.join(i.name for i in images)})" if images else ""))

    info = probe(src)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    dur = float(info["format"]["duration"])
    print(f"\n{src.name}: {v['width']}x{v['height']} {v['r_frame_rate']} "
          f"{v['codec_name']}  {dur:.2f}s  {int(info['format']['size'])/1e6:.0f} MB")

    digest = hashlib.sha256(src.read_bytes()).hexdigest()
    out = work / "raw_transcript.json"
    meta = work / "ingest.json"
    if out.exists() and meta.exists():
        prev = json.loads(meta.read_text())
        if prev.get("sha256") == digest:
            print("\ntranscript already present for this exact file - skipping "
                  "transcription (the expensive step)")
            return 0

    audio = extract_audio(src, work / "audio.mp3")
    payload = transcribe(audio, C.load_env())
    out.write_text(json.dumps(payload, indent=2))

    words = [w for w in payload.get("words", []) if w.get("type") == "word"]
    meta.write_text(json.dumps({
        "project": project, "source": src.name, "sha256": digest,
        "duration_s": round(dur, 3), "width": v["width"], "height": v["height"],
        "images": [i.name for i in images], "words": len(words),
        "language": payload.get("language_code"),
    }, indent=2))
    print(f"\n{len(words)} words, {payload.get('language_code')} "
          f"({payload.get('language_probability', 0):.2f})")
    print(f"wrote {out.name} and {meta.name}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python3 -m pipelines.video.ingest <project>")
    sys.exit(main(sys.argv[1]))
