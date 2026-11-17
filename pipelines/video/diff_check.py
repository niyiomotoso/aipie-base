"""Deterministic checks of a proposed cut against the original transcript.

Feeds the adversarial reviewer hard facts so it argues from evidence rather than
impression. Finds nothing by judgement; it only measures.

Checks:
  1. Vocabulary loss  - content words in the original that survive nowhere in the cut
  2. Dangling refs    - a span opening on a pronoun with no antecedent before it
  3. Surviving dupes  - kept spans that still open alike
  4. Clause breaks    - spans starting or ending mid-clause
  5. Coverage         - how much was dropped, and in how many runs

Writes cut-review.json for the reviewer agent to read.
"""
import difflib
import json
import pathlib
import re
import string
import sys

from . import config as C
from .takes import load_words, norm, segment, opening_match, ts

STOP = {
    "a", "an", "the", "and", "or", "but", "so", "as", "at", "by", "for", "from",
    "in", "into", "of", "on", "to", "with", "about", "that", "this", "these",
    "those", "is", "was", "are", "were", "be", "been", "being", "am", "has",
    "have", "had", "do", "does", "did", "will", "would", "can", "could", "should",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "his", "its", "our", "their", "not", "no", "yes", "if", "then",
    "than", "when", "where", "what", "which", "who", "how", "why", "all", "any",
    "some", "more", "most", "very", "just", "like", "also", "even", "only", "now",
    "here", "there", "really", "actually", "basically", "know", "think", "going",
    "get", "got", "say", "said", "one", "two", "thing", "things", "something",
    "because", "right", "okay", "well", "mean", "means", "kind", "sort", "lot",
    "you're", "it's", "there's", "that's", "don't", "doesn't", "didn't", "i'm",
    "we're", "they're", "can't", "won't", "let's", "yeah", "uh", "um",
}
PRONOUNS = {"she", "he", "it", "they", "her", "him", "them", "this", "that",
            "these", "those", "his", "hers", "its", "their"}


def content_words(text: str) -> set:
    t = text.lower().translate(str.maketrans("", "", string.punctuation))
    return {w for w in re.split(r"\s+", t) if w and w not in STOP and len(w) > 2}


def kept_dropped(words: list, plan: dict):
    kept, dropped = [], []
    for w in words:
        inside = any(s["in"] <= w["start"] <= s["out"] for s in plan["spans"])
        (kept if inside else dropped).append(w)
    return kept, dropped


def check(project: str, plan_path: pathlib.Path = None) -> dict:
    work = C.project_dir(project)
    plan = json.loads((plan_path or work / "master-plan.json").read_text())
    words = load_words(project)
    kept, dropped = kept_dropped(words, plan)

    kept_text = " ".join(w["text"] for w in kept)
    orig_text = " ".join(w["text"] for w in words)
    kept_vocab, orig_vocab = content_words(kept_text), content_words(orig_text)

    findings = []

    # 1. vocabulary that exists nowhere in the cut
    lost = sorted(orig_vocab - kept_vocab)
    lost_detail = []
    for term in lost:
        hits = [w for w in dropped if term in w["text"].lower()]
        if not hits:
            continue
        i = words.index(hits[0])
        lost_detail.append({
            "term": term, "occurrences": len(hits),
            "first_at": round(hits[0]["start"], 2),
            "context": " ".join(x["text"] for x in words[max(0, i-9):i+10]),
        })
    if lost_detail:
        findings.append({
            "check": "vocabulary_loss",
            "note": "present in the original, absent from the cut. Some of this is "
                    "redundancy being removed, which is correct. Any term the cut "
                    "later REFERS to is a defect.",
            "items": lost_detail,
        })

    # 2. a span opening on a pronoun with no antecedent in the cut before it
    dangling = []
    running = []
    for n, s in enumerate(plan["spans"]):
        inside = [w for w in words if s["in"] <= w["start"] <= s["out"]]
        if not inside:
            continue
        opening = [w["text"].strip(string.punctuation).lower() for w in inside[:5]]
        pro = next((p for p in opening[:3] if p in PRONOUNS), None)
        if pro and n > 0:
            before = " ".join(running[-40:])
            proper = re.findall(r"\b[A-Z][a-z]{2,}\b", before)
            dangling.append({
                "span": s["label"], "opens_with": " ".join(w["text"] for w in inside[:6]),
                "pronoun": pro, "at": ts(s["in"]),
                "antecedent_candidates": sorted(set(proper))[-6:],
                "preceding_cut_text": before[-220:],
            })
        running += [w["text"] for w in inside]
    if dangling:
        findings.append({
            "check": "dangling_reference",
            "note": "these spans open on a pronoun. Confirm its referent is present "
                    "and unambiguous in the cut text immediately before it.",
            "items": dangling,
        })

    # 3. UNDER-CUT: duplicates that survived, measured four ways.
    # Opening similarity alone misses the important case - two tellings of the same
    # beat that share almost no wording. Content overlap catches those.
    dupes = []
    span_tokens = []
    for s in plan["spans"]:
        inside = [w for w in words if s["in"] <= w["start"] <= s["out"]]
        toks = norm(" ".join(w["text"] for w in inside))
        span_tokens.append((s["label"], toks, {t for t in toks
                                               if t not in STOP and len(t) > 2}))
    for a in range(len(span_tokens)):
        for b in range(a + 1, len(span_tokens)):
            la, ta, ca = span_tokens[a]
            lb, tb, cb = span_tokens[b]
            if not ca or not cb:
                continue
            opening = opening_match(ta, tb)
            whole = difflib.SequenceMatcher(None, ta, tb).ratio()
            inter = ca & cb
            jaccard = len(inter) / len(ca | cb)
            contain = len(inter) / min(len(ca), len(cb))
            # Ordered overlap against the SHORTER span is the signal that survives
            # a retelling being longer than the original. Ratios against the union
            # get diluted by whatever new material the second version adds.
            seq_a = [t for t in ta if t not in STOP and len(t) > 2]
            seq_b = [t for t in tb if t not in STOP and len(t) > 2]
            matched = sum(bl.size for bl in
                          difflib.SequenceMatcher(None, seq_a, seq_b).get_matching_blocks())
            ordered = matched / min(len(seq_a), len(seq_b)) if seq_a and seq_b else 0.0
            enough = len(inter) >= 6      # guards against short spans coinciding
            why = []
            if opening >= 0.60:
                why.append("open alike")
            if whole >= 0.45:
                why.append("same wording throughout")
            if jaccard >= 0.30:
                why.append("same subject matter")
            if contain >= 0.45 and enough:
                why.append("one is largely contained in the other")
            if ordered >= 0.40 and enough:
                why.append("same points in the same order - likely a retelling")
            if why:
                dupes.append({
                    "a": la, "b": lb, "signals": why,
                    "opening_similarity": round(opening, 3),
                    "whole_similarity": round(whole, 3),
                    "content_jaccard": round(jaccard, 3),
                    "containment": round(contain, 3),
                    "ordered_overlap": round(ordered, 3),
                    "shared_terms": sorted(inter)[:14],
                })
    if dupes:
        findings.append({
            "check": "surviving_duplicate",
            "note": "UNDER-CUT: two kept spans may say the same thing. Content "
                    "overlap catches retellings that share no wording, which no "
                    "opening comparison can. Read both and decide if one is a repeat.",
            "items": dupes})

    # 3b. UNDER-CUT: a phrase repeated inside the cut itself
    kept_tokens = [t for t in norm(kept_text)]
    seen_ngrams, repeats = {}, []
    N = 5
    for i in range(len(kept_tokens) - N + 1):
        g = tuple(kept_tokens[i:i + N])
        if sum(1 for t in g if t not in STOP) < 3:
            continue
        seen_ngrams.setdefault(g, []).append(i)
    for g, pos in seen_ngrams.items():
        if len(pos) > 1:
            repeats.append({"phrase": " ".join(g), "times": len(pos),
                            "word_positions": pos})
    if repeats:
        findings.append({
            "check": "repeated_phrase",
            "note": "UNDER-CUT: this exact phrase occurs more than once in the cut. "
                    "Sometimes deliberate emphasis, often a take that was kept twice.",
            "items": sorted(repeats, key=lambda r: -r["times"])[:12]})

    # 4. spans that start or end mid-clause
    breaks = []
    for s in plan["spans"]:
        inside = [w for w in words if s["in"] <= w["start"] <= s["out"]]
        if not inside:
            continue
        last = inside[-1]["text"].rstrip()
        first = inside[0]["text"].strip(string.punctuation).lower()
        if not last.endswith((".", "?", "!", ",")):
            breaks.append({"span": s["label"], "issue": "ends mid-clause",
                           "tail": " ".join(w["text"] for w in inside[-6:])})
        if first in {"and", "but", "so", "or", "because", "which", "that"}:
            breaks.append({"span": s["label"], "issue": "opens on a conjunction",
                           "head": " ".join(w["text"] for w in inside[:6])})
    if breaks:
        findings.append({"check": "clause_break",
                         "note": "may be fine in speech; flag only if it reads broken.",
                         "items": breaks})

    # 5. coverage
    runs, prev_in = 0, True
    for w in words:
        now_in = any(s["in"] <= w["start"] <= s["out"] for s in plan["spans"])
        if prev_in and not now_in:
            runs += 1
        prev_in = now_in

    report = {
        "project": project,
        "original_words": len(words),
        "kept_words": len(kept),
        "dropped_words": len(dropped),
        "dropped_pct": round(len(dropped) / len(words) * 100, 1),
        "dropped_runs": runs,
        "original_transcript": orig_text,
        "cut_transcript": kept_text,
        "findings": findings,
    }
    (work / "cut-review.json").write_text(json.dumps(report, indent=2))
    return report


def main(project: str, plan_path: str = None) -> int:
    r = check(project, pathlib.Path(plan_path) if plan_path else None)
    print(f"=== deterministic cut check: {r['project']}")
    print(f"  original {r['original_words']}w -> cut {r['kept_words']}w "
          f"({r['dropped_pct']}% dropped across {r['dropped_runs']} runs)")
    if not r["findings"]:
        print("  no mechanical findings (this does NOT mean the cut is good)")
    for f in r["findings"]:
        print(f"\n  [{f['check']}] {len(f['items'])} item(s)")
        print(f"    {f['note']}")
        for it in f["items"][:8]:
            if f["check"] == "vocabulary_loss":
                print(f"      - {it['term']!r} x{it['occurrences']} at {it['first_at']}s")
                print(f"          ...{it['context']}...")
            elif f["check"] == "dangling_reference":
                print(f"      - {it['span']} opens {it['opens_with']!r} "
                      f"(pronoun {it['pronoun']!r})")
                print(f"          candidates before it: {it['antecedent_candidates']}")
            else:
                print(f"      - {it}")
    print(f"\nwrote cut-review.json")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python3 -m pipelines.video.diff_check <project> [plan.json]")
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
