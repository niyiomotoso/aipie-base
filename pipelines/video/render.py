"""Build and run the one-pass render: cut, transitions, B-roll, captions.

Validates before encoding and REFUSES on any failure - a bad render costs minutes
and a wrong one costs trust. Always renders from the original source; never onto an
already-encoded intermediate, which stacks generation loss.
"""
import json
import pathlib
import subprocess
import sys

from . import config as C
from .captions import render_strip
from .ingest import safe_input

VF = "setpts=PTS-STARTPTS,fps=30,format=yuv420p,setsar=1"


def join_windows(plan: dict) -> list:
    out = []
    for i, j in enumerate(plan["joins"]):
        start = plan["cutmap"][i + 1]["out_start"]
        out.append((start, start + j["frames"] / C.FPS, j["transition"]))
    return out


def validate(plan: dict, broll: list, assets: dict) -> list:
    problems = []
    for s in plan["spans"]:
        if s["out"] <= s["in"]:
            problems.append(f"{s['label']}: empty span")
    for i, j in enumerate(plan["joins"]):
        room = min(plan["spans"][i]["h_out"], plan["spans"][i + 1]["h_in"])
        if j["frames"] / C.FPS > room + 1e-6:
            problems.append(
                f"join {i} ({j['transition']} {j['frames']}f) exceeds "
                f"{room*1000:.0f}ms of handle - would clip speech")
    for b in broll:
        a = assets.get(b["slug"])
        if not a:
            problems.append(f"{b['slug']}: not in assets.json")
            continue
        if not pathlib.Path(a["local_path"]).exists():
            problems.append(f"{b['slug']}: file missing ({a['local_path']})")
        if not a.get("license_code"):
            problems.append(f"{b['slug']}: no licence recorded")
        for js, je, tr in join_windows(plan):
            if b["in"] < je and b["out"] > js:
                problems.append(
                    f"{b['slug']} ({b['in']:.2f}-{b['out']:.2f}) straddles the {tr} "
                    f"join at {js:.2f}-{je:.2f} - the transition would be hidden")
    return problems


def build_graph(plan: dict, broll: list, assets: dict, strip_idx: int) -> tuple:
    parts, inputs = [], []
    for i, s in enumerate(plan["spans"]):
        parts.append(f"[0:v]trim={s['in']}:{s['out']},{VF}[v{i}]")
        parts.append(f"[0:a]atrim={s['in']}:{s['out']},asetpts=PTS-STARTPTS[a{i}]")

    run = plan["spans"][0]["out"] - plan["spans"][0]["in"]
    vcur, acur = "v0", "a0"
    for i, j in enumerate(plan["joins"]):
        d = j["frames"] / C.FPS
        nv, na = f"vx{i}", f"ax{i}"
        parts.append(f"[{vcur}][v{i+1}]xfade=transition={j['transition']}:"
                     f"duration={round(d,4)}:offset={round(run-d,4)}[{nv}]")
        parts.append(f"[{acur}][a{i+1}]acrossfade=d={round(d,4)}[{na}]")
        vcur, acur = nv, na
        run = round(run + (plan["spans"][i+1]["out"] - plan["spans"][i+1]["in"]) - d, 4)

    cur = vcur
    for n, b in enumerate(broll):
        idx = n + 1
        inputs += ["-loop", "1", "-framerate", str(C.FPS),
                   "-t", f"{b['out']-b['in']:.3f}", "-i", assets[b["slug"]]["local_path"]]
        lab, nxt = f"br{n}", f"ov{n}"
        if b.get("style", "full") == "full":
            parts.append(
                f"[{idx}:v]scale={C.W*2}:{C.H*2}:force_original_aspect_ratio=increase,"
                f"crop={C.W*2}:{C.H*2},zoompan=z='min(1+0.0009*on,1.13)':"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={C.W}x{C.H}:"
                f"fps={C.FPS},setsar=1[{lab}]")
            pos = "0:0"
        else:
            parts.append(
                f"[{idx}:v]scale={C.INSET_W*2}:{C.INSET_H*2}:"
                f"force_original_aspect_ratio=increase,crop={C.INSET_W*2}:{C.INSET_H*2},"
                f"zoompan=z='min(1+0.0010*on,1.14)':x='iw/2-(iw/zoom/2)':"
                f"y='ih/2-(ih/zoom/2)':d=1:s={C.INSET_W}x{C.INSET_H}:fps={C.FPS},"
                f"pad={C.INSET_W+2*C.INSET_BORDER}:{C.INSET_H+2*C.INSET_BORDER}:"
                f"{C.INSET_BORDER}:{C.INSET_BORDER}:white,setsar=1[{lab}]")
            pos = f"{C.INSET_X}:{C.INSET_Y}"
        parts.append(f"[{cur}][{lab}]overlay={pos}:"
                     f"enable='between(t,{b['in']:.3f},{b['out']:.3f})'[{nxt}]")
        cur = nxt

    # captions last, so they survive every cutaway
    parts.append(f"[{cur}][{strip_idx}:v]overlay=0:{C.STRIP_TOP}:format=yuv420,"
                 f"format=yuv420p[vout]")
    return ";".join(parts), inputs, acur


def main(project: str, visuals: bool = False) -> int:
    work = C.project_dir(project)
    plan = json.loads((work / "master-plan.json").read_text())
    phrases = json.loads((work / "captions.json").read_text())["phrases"]
    meta = json.loads((work / "ingest.json").read_text())
    src = work / "source" / meta["source"]

    broll, assets = [], {}
    if visuals:
        bf, af = work / "broll.json", work / "assets.json"
        if not (bf.exists() and af.exists()):
            raise SystemExit("visuals requested but broll.json / assets.json missing")
        broll = json.loads(bf.read_text())
        assets = {a["slug"]: a for a in json.loads(af.read_text())}

    problems = validate(plan, broll, assets)
    print("=== validation")
    for b in broll:
        print(f"  {b['slug']:<14} {b['in']:7.2f}-{b['out']:7.2f} "
              f"{b.get('style','full'):5}  {assets[b['slug']]['license_code']}")
    if problems:
        print("\nREFUSING TO RENDER:")
        for p in problems:
            print("  - " + p)
        return 1
    print("  all edges clear, every asset present and licensed\n")

    strip = work / "strip"
    uniq = render_strip(phrases, plan["duration_s"], strip)
    print(f"caption strip: {int(plan['duration_s']*C.FPS)} frames, {uniq} unique states")

    graph, inputs, acur = build_graph(plan, broll, assets, len(broll) + 1)
    suffix = "-final-visuals" if visuals else "-final"
    out = work / f"{project.lower()}{suffix}.mp4"
    cmd = (["ffmpeg", "-v", "error", "-stats", "-y"] + safe_input(src) + inputs
           + ["-framerate", str(C.FPS), "-i", str(strip / "%06d.png"),
              "-filter_complex", graph, "-map", "[vout]", "-map", f"[{acur}]"]
           + C.VIDEO_ARGS + C.AUDIO_ARGS + ["-movflags", "+faststart", str(out)])
    if subprocess.run(cmd).returncode != 0:
        return 1
    for old in strip.glob("*.png"):
        old.unlink()
    strip.rmdir()

    info = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
         "-show_entries", "stream=nb_read_packets,width,height",
         "-show_entries", "format=duration,size", "-of", "json", str(out)],
        capture_output=True, text=True).stdout)
    s0, f0 = info["streams"][0], info["format"]
    pk, dur = int(s0["nb_read_packets"]), float(f0["duration"])
    print(f"\n{out.name}: {s0['width']}x{s0['height']}  {int(f0['size'])/1e6:.1f} MB")
    print(f"  {pk} frames = {pk/C.FPS:.3f}s   container {dur:.3f}s   "
          f"plan {plan['duration_s']:.3f}s   drift {abs(dur-plan['duration_s'])*1000:.0f}ms")
    if broll:
        bs = sum(b["out"] - b["in"] for b in broll)
        print(f"  B-roll {bs:.1f}s = {bs/plan['duration_s']*100:.0f}% of runtime")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python3 -m pipelines.video.render <project> [--visuals]")
    sys.exit(main(sys.argv[1], "--visuals" in sys.argv))
