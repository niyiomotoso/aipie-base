"""Turn the model's proposed cut into a validated plan.

Input  : data/video/<project>/selects.json, written by the model -
         {"spans": [{"lo":, "hi":, "label":}], "joins": [{"transition":, "frames":, "reason":}]}
         lo/hi are approximate windows; this snaps them to the words inside.
Output : master-plan.json (spans with handles, capped joins, cut map)
         final-transcript.txt (exactly what the cut will say)

The model never computes a cut point. It names the words it wants; this works out
where the frames actually fall and refuses anything that would clip speech.
"""
import json
import pathlib
import sys

from . import config as C
from .takes import load_words, ts


def build(project: str) -> dict:
    work = C.project_dir(project)
    sel_f = work / "selects.json"
    if not sel_f.exists():
        raise SystemExit(
            f"no selects.json at {sel_f}\n"
            "The model writes it: {\"spans\":[{\"lo\":..,\"hi\":..,\"label\":\"..\"}],"
            " \"joins\":[{\"transition\":\"fadeblack\",\"frames\":3,\"reason\":\"..\"}]}")
    sel = json.loads(sel_f.read_text())
    windows, want = sel["spans"], sel["joins"]
    words = load_words(project)

    if len(want) != len(windows) - 1:
        raise SystemExit(f"{len(windows)} spans needs {len(windows)-1} joins, "
                         f"got {len(want)}")

    # --- snap to words, grow handles into whatever silence exists ------------
    spans = []
    for w in windows:
        inside = [x for x in words if w["lo"] <= x["start"] <= w["hi"]]
        if not inside:
            raise SystemExit(f"{w['label']}: no words between {w['lo']} and {w['hi']}")
        first, last = inside[0]["start"], inside[-1]["end"]
        before = [x["end"] for x in words if x["end"] <= first + 1e-9]
        after = [x["start"] for x in words if x["start"] >= last - 1e-9]
        lead = first - max(before) if before else C.MAX_HANDLE
        trail = (min(after) - last) if after else C.MAX_HANDLE
        h_in = max(0.0, min(C.MAX_HANDLE, lead * C.HANDLE_SHARE))
        h_out = max(0.0, min(C.MAX_HANDLE, trail * C.HANDLE_SHARE))
        spans.append({"label": w["label"], "first": first, "last": last,
                      "in": round(first - h_in, 4), "out": round(last + h_out, 4),
                      "h_in": round(h_in, 4), "h_out": round(h_out, 4),
                      "words": len(inside)})

    # --- cap every transition to the handles it sits between -----------------
    joins, capped = [], []
    for i, j in enumerate(want):
        trans = j.get("transition", C.DEFAULT_TRANSITION)
        if trans not in C.TRANSITIONS:
            raise SystemExit(f"join {i}: unknown transition {trans!r}; "
                             f"allowed: {', '.join(C.TRANSITIONS)}")
        wanted = int(j.get("frames", C.TRANSITIONS[trans]))
        room = min(spans[i]["h_out"], spans[i + 1]["h_in"])
        frames = max(1, min(wanted, int(room * C.FPS)))
        if frames < wanted:
            capped.append((i, trans, wanted, frames, room * 1000))
        joins.append({"transition": trans, "frames": frames, "wanted": wanted,
                      "room_ms": round(room * 1000, 1),
                      "reason": j.get("reason", "")})

    # --- durations and the source->output cut map ----------------------------
    run = spans[0]["out"] - spans[0]["in"]
    cutmap = [{"label": spans[0]["label"], "out_start": 0.0, "src_in": spans[0]["in"]}]
    for i, j in enumerate(joins):
        d = j["frames"] / C.FPS
        offset = round(run - d, 4)
        cutmap.append({"label": spans[i + 1]["label"], "out_start": offset,
                       "src_in": spans[i + 1]["in"]})
        run = round(run + (spans[i + 1]["out"] - spans[i + 1]["in"]) - d, 4)

    plan = {"project": project, "spans": spans, "joins": joins, "cutmap": cutmap,
            "duration_s": round(run, 3), "fps": C.FPS}
    return plan, capped, words


def transcript(project: str, plan: dict, words: list) -> str:
    lines, flow, t = [], [], 0.0
    for i, s in enumerate(plan["spans"]):
        if i:
            t -= plan["joins"][i - 1]["frames"] / C.FPS
        txt = " ".join(w["text"] for w in words
                       if s["in"] <= w["start"] <= s["out"]).strip()
        lines.append((ts(t), s["label"], txt))
        flow.append(txt)
        t += s["out"] - s["in"]
    body = " ".join(flow)
    return ("FINAL CUT TRANSCRIPT\n\n"
            + "\n\n".join(f"{a}  {b}\n{c}" for a, b, c in lines)
            + f"\n\n---\n{len(body.split())} words, runtime {ts(t)}\n\n"
              f"CONTINUOUS READ:\n\n{body}\n")


def main(project: str) -> int:
    plan, capped, words = build(project)
    work = C.project_dir(project)

    print("=== spans (handles grown into source silence)")
    for s in plan["spans"]:
        print(f"  {s['label'][:22]:<22} {s['in']:8.3f} -> {s['out']:8.3f}  "
              f"handles {s['h_in']*1000:5.0f}/{s['h_out']*1000:5.0f}ms  {s['words']:>3}w")

    print("\n=== joins")
    mix = {}
    for i, j in enumerate(plan["joins"]):
        mix[j["transition"]] = mix.get(j["transition"], 0) + 1
        flag = "" if j["frames"] == j["wanted"] else \
               f"   <- wanted {j['wanted']}f, only {j['room_ms']:.0f}ms of handle"
        print(f"  {plan['spans'][i]['label'][:14]:<14} -> "
              f"{plan['spans'][i+1]['label'][:14]:<14} "
              f"{j['transition']:<10} {j['frames']}f{flag}")
        if j["reason"]:
            print(f"      {j['reason']}")
    print(f"\n  mix: {mix}")
    if capped:
        print("  (a cap is physics, not a bug - there was not enough silence)")

    dur = plan["duration_s"]
    print(f"\nduration {int(dur//60)}:{dur%60:06.3f}")

    (work / "master-plan.json").write_text(json.dumps(plan, indent=2))
    txt = transcript(project, plan, words)
    (work / "final-transcript.txt").write_text(txt)
    print(f"wrote master-plan.json and final-transcript.txt")
    print("\nSTOP. Send final-transcript.txt to Niyi and wait for approval "
          "before rendering.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python3 -m pipelines.video.plan <project>")
    sys.exit(main(sys.argv[1]))
