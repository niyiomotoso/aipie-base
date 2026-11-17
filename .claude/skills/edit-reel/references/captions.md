# Caption spec

Burned-in, word-highlight style. Chosen after comparing four treatments rendered
over real footage.

## Why Pillow and not drawtext

This machine's ffmpeg is the slim Homebrew bottle: **no `drawtext`, no `subtitles`,
no `ass` filter.** Captions are drawn by Pillow as RGBA and composited with
`overlay`. That is not a workaround to tolerate — it is what makes per-word
highlighting possible, which `drawtext` cannot do.

Check with `ffmpeg -hide_banner -filters | grep -E 'drawtext|subtitles'`. If a
future `ffmpeg-full` makes them available, the Pillow path is still preferred.

## Timing: source time is not output time

Word timestamps are in **source** time. Captions need **output** time. On a reel
where four minutes were cut, the drift grows through the video. Map through the cut
map every time:

```
output_t = span.out_start + (source_t - span.src_in)
```

`master-plan.json` carries `cutmap` for exactly this. Verified against a cold
readback of the finished file: predicted 0.250 / 0.370 / 0.550, measured 0.280 /
0.400 / 0.580 — within 30ms.

## Phrasing

A fixed word cap breaks on function words — "something **I**", "interesting
**about**" — which reads badly in every visual style. Score each candidate break
instead:

```
+3.0  last word ends a sentence (. ? !)
+1.0  last word ends with a comma
+    min(1.5, gap_to_next * 3.0)      a real pause is a real break
-2.0  last word is a continuer (pronoun, article, preposition, conjunction, aux)
+0.4  phrase is 3-4 words
```

Take 2–5 words, pick the highest scoring break, repeat. Force a break where the gap
exceeds 0.70s.

**This is still imperfect** — phrases will occasionally open on a preposition. It is
a heuristic standing in for judgement, and worth revisiting. Do not present it as
solved.

## Layout

| Property | Value | Why |
|---|---|---|
| Bottom edge | y 1530 of 1920 | **Fixed.** Text grows upward from it |
| Clearance below | 390px, 20% | Clears Instagram's caption and action area |
| Max text width | 880px | Clears the right-hand action rail |
| Font | Arial Black, 68px | No Inter or Montserrat installed |
| Stroke | 7px, black at 92% | Holds over light and dark shots |
| Live word | `#FFD24A` | Warm amber, reads against both |
| Line gap | 14px | |

**Anchor the bottom edge, never the centre.** Centring on a midpoint makes one-line
and two-line phrases sit at different heights, so the block jumps on every wrap. On
real footage the line count alternated between 1 and 2 constantly — it looked like
shaking, and that is exactly what he reported.

## Highlighting

Match the live word **by index, not by text.** Matching by text lights every
occurrence when a phrase repeats a word.

## Rendering efficiently

The image only changes when the lit word changes. Cache by `(phrase, live_index)`
and reuse — 4,822 frames needed only 677 unique states.

Draw a **strip**, not a full frame. The block only occupies the bottom fifth, so
render 1080×320 at y 1240 and overlay at that offset.

## Composite order

```
cut → B-roll → captions
```

Captions go on **top**, so they survive every cutaway. Use
`overlay=0:1240:format=yuv420` explicitly — `format=auto` forces an RGB round trip
that costs real quality.

## Sidecar

Also write a `.srt` from the same phrases. The `srt` muxer exists even in the slim
build, and some platforms take soft subtitles.
