"""Caption phrasing and frame rendering.

ffmpeg here has no drawtext/subtitles/ass filter, so captions are drawn by Pillow
and composited with overlay. That constraint is what makes per-word highlighting
possible at all.

Two rules that are easy to get wrong and look like bugs:
  - the block anchors to a FIXED BOTTOM edge and grows upward. Centring makes it
    jump every time a phrase wraps to two lines.
  - the live word is matched by INDEX, not by text, or a repeated word lights twice.
"""
import json
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

from . import config as C
from .takes import load_words

CONTINUERS = {
    "i", "we", "you", "he", "she", "it", "they", "the", "a", "an", "my", "his", "her",
    "their", "its", "of", "to", "in", "on", "for", "with", "at", "by", "from", "about",
    "and", "or", "but", "so", "as", "that", "this", "these", "those", "is", "was",
    "are", "were", "has", "have", "had", "been", "being", "will", "would", "can",
    "could", "like", "just", "very", "some", "any", "all", "more", "most", "what",
    "when", "where", "how", "why", "who", "we're", "you're", "it's", "there's",
}

_font = None


def font():
    global _font
    if _font is None:
        _font = ImageFont.truetype(C.CAPTION_FONT, C.CAPTION_SIZE)
    return _font


def to_output_time(plan: dict, words: list) -> list:
    """Word timestamps are in SOURCE time; captions need OUTPUT time."""
    out = []
    for s, cm in zip(plan["spans"], plan["cutmap"]):
        for w in words:
            if s["in"] <= w["start"] <= s["out"]:
                out.append({"text": w["text"],
                            "start": round(cm["out_start"] + (w["start"] - cm["src_in"]), 4),
                            "end": round(cm["out_start"] + (w["end"] - cm["src_in"]), 4)})
    out.sort(key=lambda w: w["start"])
    return out


def break_score(seq: list, nxt) -> float:
    last = seq[-1]["text"].rstrip()
    bare = last.strip(".,?!’'\"").lower()
    s = 0.0
    if last.endswith((".", "?", "!")):
        s += 3.0
    elif last.endswith(","):
        s += 1.0
    s += min(1.5, (nxt["start"] - seq[-1]["end"]) * 3.0) if nxt else 3.0
    if bare in CONTINUERS:
        s -= 2.0
    if 3 <= len(seq) <= 4:
        s += 0.4
    return s


def phrase(words: list) -> list:
    """A fixed word cap breaks on function words; score each candidate instead."""
    out, i = [], 0
    while i < len(words):
        best, best_s = None, None
        for n in range(C.PHRASE_MIN, C.PHRASE_MAX + 1):
            seq = words[i:i + n]
            if not seq:
                break
            nxt = words[i + n] if i + n < len(words) else None
            if len(seq) > 1 and seq[-1]["start"] - seq[-2]["end"] > C.PHRASE_GAP:
                seq = seq[:-1]
                nxt = words[i + len(seq)] if i + len(seq) < len(words) else None
            s = break_score(seq, nxt)
            if best_s is None or s > best_s:
                best, best_s = seq, s
        out.append(best)
        i += len(best)
    return out


def wrap(draw, text: str) -> list:
    out, line = [], []
    for word in text.split():
        if draw.textlength(" ".join(line + [word]), font=font()) <= C.CAPTION_SAFE_W \
                or not line:
            line.append(word)
        else:
            out.append(" ".join(line))
            line = [word]
    if line:
        out.append(" ".join(line))
    return out


def draw_frame(text: str, live_idx) -> Image.Image:
    img = Image.new("RGBA", (C.W, C.STRIP_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    lines = wrap(d, text)
    hgt = len(lines) * C.CAPTION_SIZE + (len(lines) - 1) * C.LINE_GAP
    y = (C.CAPTION_BOTTOM - C.STRIP_TOP) - hgt      # fixed bottom, grows upward
    idx = 0
    for ln in lines:
        x = C.W / 2 - d.textlength(ln, font=font()) / 2
        for tok in ln.split():
            d.text((x, y), tok, font=font(),
                   fill=C.ACCENT if idx == live_idx else C.WHITE,
                   stroke_width=C.CAPTION_STROKE, stroke_fill=C.STROKE_COLOR)
            x += d.textlength(tok + " ", font=font())
            idx += 1
        y += C.CAPTION_SIZE + C.LINE_GAP
    return img


def render_strip(phrases: list, duration: float, dest: pathlib.Path) -> int:
    """One PNG per output frame. Cached by (phrase, live word) - the image only
    changes when the lit word changes, so most frames are repeats."""
    dest.mkdir(parents=True, exist_ok=True)
    for old in dest.glob("*.png"):
        old.unlink()
    n = int(round(duration * C.FPS))
    blank = Image.new("RGBA", (C.W, C.STRIP_H), (0, 0, 0, 0))
    cache = {}
    for i in range(n):
        t = i / C.FPS
        act = next((p for p in phrases
                    if p[0]["start"] <= t <= p[-1]["end"] + 0.12), None)
        if act is None:
            blank.save(dest / f"{i:06d}.png")
            continue
        live = next((k for k, x in enumerate(act) if x["start"] <= t <= x["end"]), None)
        key = (id(act), live)
        if key not in cache:
            cache[key] = draw_frame(" ".join(x["text"] for x in act), live)
        cache[key].save(dest / f"{i:06d}.png")
    return len(cache)


def srt(phrases: list) -> str:
    def stamp(s):
        h, rem = divmod(s, 3600)
        m, sec = divmod(rem, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(sec):02d},{int(round((sec%1)*1000)):03d}"
    return "".join(
        f"{n}\n{stamp(p[0]['start'])} --> {stamp(p[-1]['end'])}\n"
        f"{' '.join(x['text'] for x in p)}\n\n"
        for n, p in enumerate(phrases, 1))


def main(project: str) -> int:
    work = C.project_dir(project)
    plan = json.loads((work / "master-plan.json").read_text())
    words = to_output_time(plan, load_words(project))
    phrases = phrase(words)
    (work / "captions.json").write_text(json.dumps(
        {"phrases": phrases,
         "rules": {"min": C.PHRASE_MIN, "max": C.PHRASE_MAX, "gap_s": C.PHRASE_GAP}},
        indent=2))
    (work / f"{project.lower()}-final.srt").write_text(srt(phrases))
    print(f"{len(words)} words in output time -> {len(phrases)} phrases")
    for p in phrases[:8]:
        print(f"  {p[0]['start']:6.2f}-{p[-1]['end']:6.2f}  "
              f"{' '.join(x['text'] for x in p)}")
    print("  ...")
    print(f"wrote captions.json and {project.lower()}-final.srt")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python3 -m pipelines.video.captions <project>")
    sys.exit(main(sys.argv[1]))
