"""Verify the finished file, not the plan.

The headline check is a cold readback: re-transcribe the output and confirm each
intended removal is actually absent and the opening and closing lines are present.
A plan that looks right can still lose a word.
"""
import json
import pathlib
import subprocess
import sys

from . import config as C
from .ingest import extract_audio, transcribe


def detect(path: pathlib.Path) -> dict:
    def run(args):
        return subprocess.run(["ffmpeg", "-v", "error", "-i", str(path)] + args
                              + ["-f", "null", "-"],
                              capture_output=True, text=True).stderr
    black = run(["-vf", "blackdetect=d=0.04:pix_th=0.12", "-an"])
    freeze = run(["-vf", "freezedetect=n=-50dB:d=0.5", "-an"])
    silence = run(["-af", "silencedetect=n=-45dB:d=0.6", "-vn"])
    return {
        "black_spans": black.count("black_start"),
        "freeze_spans": freeze.count("freeze_start"),
        "silence_spans": silence.count("silence_start"),
    }


def main(project: str, visuals: bool = False) -> int:
    work = C.project_dir(project)
    plan = json.loads((work / "master-plan.json").read_text())
    suffix = "-final-visuals" if visuals else "-final"
    video = work / f"{project.lower()}{suffix}.mp4"
    if not video.exists():
        raise SystemExit(f"no render at {video}")

    expected = (work / "final-transcript.txt").read_text()
    expected_words = len(expected.split("CONTINUOUS READ:")[-1].split())

    print(f"=== cold readback of {video.name}")
    audio = extract_audio(video, work / "readback.mp3")
    payload = transcribe(audio, C.load_env())
    heard = [w for w in payload.get("words", []) if w.get("type") == "word"]
    text = payload.get("text", "")

    print(f"  words heard {len(heard)} against {expected_words} planned "
          f"(a one-word difference is normal STT variance on stumbles)")
    print(f"  opens : {text[:80]!r}")
    print(f"  closes: {text[-80:]!r}")

    checks = json.loads((work / "qc-expect.json").read_text()) \
        if (work / "qc-expect.json").exists() else {}
    fails = []
    for phrase in checks.get("must_be_absent", []):
        n = text.lower().count(phrase.lower())
        print(f"  absent? {phrase!r:40} {n} occurrence(s)"
              + ("" if n == 0 else "   <- STILL PRESENT"))
        if n:
            fails.append(f"{phrase!r} should have been removed")
    for phrase in checks.get("must_be_present", []):
        n = text.lower().count(phrase.lower())
        print(f"  present? {phrase!r:39} {n} occurrence(s)"
              + ("" if n else "   <- MISSING"))
        if not n:
            fails.append(f"{phrase!r} should be present")

    print("\n=== signal checks")
    d = detect(video)
    n_dips = sum(1 for j in plan["joins"] if j["transition"] == "fadeblack")
    print(f"  black spans   {d['black_spans']:>3}  ({n_dips} fadeblack joins planned; "
          f"a 3-frame dip may be too brief to register)")
    print(f"  freeze spans  {d['freeze_spans']:>3}  (expect 0)")
    print(f"  silence >0.6s {d['silence_spans']:>3}  (expect 0 mid-speech)")
    if d["freeze_spans"]:
        fails.append("freeze detected in the output")

    (work / "qc-report.json").write_text(json.dumps(
        {"video": video.name, "words_heard": len(heard),
         "words_planned": expected_words, "signals": d,
         "failures": fails, "readback_text": text}, indent=2))

    if fails:
        print("\nQC FAILURES - do not upload:")
        for f in fails:
            print("  - " + f)
        return 1
    print("\nQC clean. Note what was NOT checked when reporting: this verifies "
          "speech and signal, not framing or caption placement - pull frames and look.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python3 -m pipelines.video.qc <project> [--visuals]")
    sys.exit(main(sys.argv[1], "--visuals" in sys.argv))
