# Cut rules

Everything here was derived from editing real footage, not from theory. Each rule
exists because its absence produced a specific defect.

## Project layout

```
Videos Unedited/<project>/        source — footage, plus any images he provides
Videos Edited/<project>/          output, name mirrors the source exactly
    <project>-final.mp4           clean cut with captions
    <project>-final-visuals.mp4   only when the visual pass ran
    <project>-final.srt           sidecar subtitles
    final-transcript.txt          what the cut says, with output timecodes
    master-plan.json              spans, joins, cut map
    captions.json                 phrases in output time
    assets.json                   rights ledger, only with visuals
    credits.txt                   attribution lines, only when any asset needs them
    titles-descriptions.txt       4 titles, 2 captions
```

Images he provides live loose in the source folder — detect by type, do not demand
a subfolder.

## Untrusted media

Footage arrives from Drive and images from the internet. Before ffprobe sees a file,
sniff its magic bytes (`1A 45 DF A3` for Matroska, `ftyp` at offset 4 for MP4/MOV),
force the demuxer, pass `-protocol_whitelist file`, `-enable_drefs 0`, and address it
as `file:<path>`. An HLS playlist or `ffconcat` list names other files and URLs and
will read them. Reuse the same input arguments for every later ffmpeg call on that
file.

## Transcription

ElevenLabs Scribe, `model_id=scribe_v1`, `timestamps_granularity=word`,
`tag_audio_events=true`. Send the **whole track in one request** — fixed-time
chunking splits words across boundaries and a split word cannot anchor a cut.
Extract audio as mono 16kHz mp3 at 48kbps first; a 7-minute track is ~2.5MB.

Redact the key from every error message before printing it.

Measured: 7 minutes of audio transcribed in 6.6s. STT did not draw down the TTS
character quota — `character_count` was identical before and after. Watch the
dashboard rather than assuming that holds.

## Segmentation and duplicate detection

Split the word stream wherever the gap between consecutive words is **≥ 0.8s**. That
yields utterances.

Cluster repeats by **opening similarity**, not whole-string similarity:

```python
def opening_match(a, b):            # a, b are normalised token lists
    n = min(len(a), len(b))
    return 0.0 if n < 4 else SequenceMatcher(None, a[:n], b[:n]).ratio()
```

A false start is a *prefix* of the completed take. Comparing full sequences fails
because a 6-word abandoned start and its 114-word completion are mostly different.
Threshold 0.70 worked on real footage.

**The keeper is usually the longest version, but not reliably.** Where two takes tie
on word count, prefer the later and more complete one. Record the reason.

### What the algorithm will miss, and you must not

- **Semantically identical takes with different wording.** Two tellings of the same
  beat that open differently will never cluster. Only reading catches them.
- **A trailing fragment at the end of a long kept segment.** An abandoned start that
  sits at the *tail* of a 30-second keeper is not its own utterance, so it never
  appears as a cluster. Read the end of every kept span.
- **An antecedent removed by a cut.** Dropping the take that introduces someone
  leaves the next take opening on "she" with nothing to refer to. Check that every
  kept span's opening pronouns still have a referent.

## Spans and handles

Define each span by its **words**, then grow it into the surrounding silence:

```
first_word_start, last_word_end       from the transcript
lead_avail  = first_word_start - previous word's end in the SOURCE
trail_avail = next word's start in the SOURCE - last_word_end
handle_in   = min(0.25, lead_avail  * 0.45)
handle_out  = min(0.25, trail_avail * 0.45)
span_in  = first_word_start - handle_in
span_out = last_word_end    + handle_out
```

Taking 45% leaves room for the neighbouring span to take its own handle from the
same silence. Capping at 250ms stops a long pause pulling in dead air.

## Transitions

Three only — `fadeblack`, `hblur`, `fade`. `fadeblack` is the house default; the
others appear occasionally where a pause would interrupt a sentence. Choose per join
and record a reason. **No hard cuts.**

Durations that worked: `fadeblack` 3 frames, `fade` 4, `hblur` 5, at 30fps.

**Cap every transition to the handles it sits between:**

```
room   = min(spans[i].handle_out, spans[i+1].handle_in)
frames = min(wanted_frames, int(room * fps))
```

A transition blends the tail of one span with the head of the next, so both sides
must have enough silence. Where speech is continuous the cap can fall to 1 frame —
that is physics, not a bug. Report it rather than overriding it.

At 3 frames `fadeblack` is asymmetric: it reaches full black for one frame then eases
up over two. Measured luma 151 → 3.1 → 84 → 151. If a more deliberate dip is wanted,
5–6 frames.

## Rendering

One pass from the original source. Build the cut as a chain of `xfade` and
`acrossfade`, then overlay B-roll, then overlay captions. Never render onto an
already-encoded intermediate.

```
-c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p
-r 30 -g 60 -keyint_min 60 -sc_threshold 0 -x264-params force-cfr=1
-c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart
```

Forced keyframe cadence with scene-cut detection off keeps parts concatenable
without re-encoding. Never use `-shortest`; sample rounding leaves the mix a few
milliseconds short and it will drop a frame.

## Verification

- **Frame count** from `ffprobe -count_packets` must match the computed duration.
- **Readback**: re-transcribe the finished file and check each intended removal is
  actually absent and each kept line present. A one-word discrepancy against plan is
  normal STT variance on hyphenated stumbles; a missing sentence is not.
- **blackdetect / freezedetect / silencedetect** on the output.
- Pull two or three frames and **look at them**.
