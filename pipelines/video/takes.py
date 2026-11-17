"""Segment the transcript into utterances and cluster repeated lines.

A false start is a PREFIX of the completed take, so compare how two utterances
OPEN rather than their full token sequences. Comparing whole strings fails because
a 6-word abandoned start and its 114-word completion are mostly different.

This under-detects on purpose. It cannot see two tellings of the same beat that
share no wording, nor a trailing fragment at the end of a long kept segment.
Those are for the model to catch by reading. See references/cut-rules.md.
"""
import difflib
import json
import pathlib
import re
import string
import sys

from . import config as C


def load_words(project: str) -> list:
    f = C.project_dir(project) / "raw_transcript.json"
    if not f.exists():
        raise SystemExit(f"no transcript - run ingest first ({f})")
    return [w for w in json.loads(f.read_text())["words"] if w.get("type") == "word"]


def norm(text: str) -> list:
    t = text.lower().translate(str.maketrans("", "", string.punctuation))
    return [x for x in re.split(r"\s+", t) if x]


def segment(words: list, gap: float = C.PAUSE_GAP) -> list:
    segs, cur = [], []
    for w in words:
        if cur and w["start"] - cur[-1]["end"] >= gap:
            segs.append(cur)
            cur = []
        cur.append(w)
    if cur:
        segs.append(cur)
    rows = []
    for i, s in enumerate(segs):
        text = " ".join(w["text"] for w in s).strip()
        rows.append({"i": i, "start": s[0]["start"], "end": s[-1]["end"],
                     "dur": s[-1]["end"] - s[0]["start"], "words": len(s),
                     "text": text, "tokens": norm(text)})
    return rows


def opening_match(a: list, b: list) -> float:
    n = min(len(a), len(b))
    return 0.0 if n < 4 else difflib.SequenceMatcher(None, a[:n], b[:n]).ratio()


def cluster(rows: list, thresh: float = C.SIMILAR) -> list:
    seen, groups = set(), []
    for a in range(len(rows)):
        if a in seen or len(rows[a]["tokens"]) < 4:
            continue
        group = [a]
        for b in range(a + 1, len(rows)):
            if b in seen or len(rows[b]["tokens"]) < 4:
                continue
            if any(opening_match(rows[m]["tokens"], rows[b]["tokens"]) >= thresh
                   for m in group):
                group.append(b)
                seen.add(b)
        if len(group) > 1:
            seen.add(a)
            groups.append(group)
    return groups


def ts(x: float) -> str:
    return f"{int(x // 60)}:{x % 60:05.2f}"


def main(project: str) -> int:
    words = load_words(project)
    rows = segment(words)
    groups = cluster(rows)

    print(f"=== {len(rows)} utterances from {len(words)} words "
          f"(split on >= {C.PAUSE_GAP}s silence)\n")
    for r in rows:
        print(f"[{r['i']:>3}] {ts(r['start'])}-{ts(r['end'])} "
              f"({r['dur']:5.1f}s, {r['words']:>3}w)  {r['text']}")

    print(f"\n=== {len(groups)} repeat groups (opening similarity >= {C.SIMILAR})")
    dropped = set()
    for g in groups:
        keeper = max(g, key=lambda i: rows[i]["words"])
        print()
        for i in g:
            r = rows[i]
            if i != keeper:
                dropped.add(i)
            print(f"  {'KEEP ' if i == keeper else 'drop '}[{r['i']:>3}] "
                  f"{ts(r['start'])} ({r['dur']:5.1f}s, {r['words']:>3}w)  {r['text'][:88]}")

    kept = [r for r in rows if r["i"] not in dropped]
    total = rows[-1]["end"] - rows[0]["start"]
    kept_dur = sum(r["dur"] for r in kept)
    print(f"\n=== algorithmic pass")
    print(f"raw        : {ts(total)}, {len(rows)} utterances, {len(words)} words")
    print(f"after drops: {ts(kept_dur)}, {len(kept)} utterances "
          f"({(1-kept_dur/total)*100:.0f}% removed)")
    print("\nNOTE: this is a candidate list, not the cut. Read every utterance -"
          "\n  duplicates that share no wording will not appear here, and a trailing"
          "\n  fragment inside a long kept segment will not either.")

    out = C.project_dir(project) / "takes.json"
    out.write_text(json.dumps(
        {"utterances": [{k: v for k, v in r.items() if k != "tokens"} for r in rows],
         "groups": groups, "algorithmic_drops": sorted(dropped)}, indent=2))
    print(f"\nwrote {out.name}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python3 -m pipelines.video.takes <project>")
    sys.exit(main(sys.argv[1]))
