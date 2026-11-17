---
name: edit-reel
description: "Edit a narrated talking-head reel from raw footage: transcribe, remove repeated takes and false starts, join with transitions, burn in captions, and optionally add B-roll. Use when Niyi says 'edit the reel', 'cut this video', 'edit <project>', or points at a folder of narration footage in Drive. For montage footage with no narration, use edit-montage instead."
argument-hint: "[project folder name, e.g. Eliza] [visuals:yes|no]"
---

# Edit a narrated reel

Raw footage in, finished reel out. The recording is the source of truth — not any
script written beforehand. This skill does not write scripts and does not post
anything.

## Core principles

1. **The model proposes, code validates, code cuts.** Never compute a cut point by
   hand or run ffmpeg from improvised arguments. Choose takes by reading the
   transcript; let `pipelines/video/` prove the choice and perform it.
2. **There is no target length.** The reel is as long as the unique content. Keep
   everything he said once; remove only repeats, false starts and abandoned
   attempts. Never trim meaning to hit a duration.
3. **Only redundancy is removed without asking.** Cutting something unique — a
   tangent that does not belong — is a deletion of his work. Propose it at the
   gate; never do it silently.
4. **Every cut edge lands in silence.** Spans carry handles; transitions consume
   handles, never speech. The validator enforces this and refuses to render.
5. **Verify the output, not the plan.** A cut that looks right on paper can still
   lose a word. Re-transcribe the finished file and read it cold before uploading.
6. **Say what you could not check.** Name the thing you did not verify rather than
   implying the whole render was inspected.

## Interaction rules

- Use `AskUserQuestion` in Claude Code (call `ToolSearch` with
  `select:AskUserQuestion` first if its schema is not loaded). Fall back to
  numbered options in chat only if the call errors. Never silently skip a question.
- **Ask only when the answer materially changes the cut, the scope or the risk and
  cannot be responsibly inferred.** Which take reads better is your judgement, not
  his. Whether a tangent should be cut is his.
- One question at a time.

## Project

<project> #$ARGUMENTS </project>

**If no project is named above, ask which one**, listing the folders under
`Videos Unedited/` in Drive. Do not proceed without one.

## Workflow

### Phase 0: Preflight and scope

#### 0.1 Check the machine before spending anything

```
python3 pipelines/video/doctor.py
```

Reports rclone remote, API keys, ffmpeg filters, disk headroom. **Stop and tell him
exactly what is missing** rather than failing halfway through a render.

#### 0.2 Resolve the project folder

Source is `Videos Unedited/<project>/`, output is `Videos Edited/<project>/` —
the names mirror exactly. Create the output folder if absent. **Never write loose
files to the root of `Videos Edited/`.** See `references/cut-rules.md` for the
layout and the file names to produce.

#### 0.3 Ask about visuals — this is a required gate

Unless the argument already says `visuals:yes` or `visuals:no`, ask whether this run
should include the B-roll pass. It changes what Phase 1 researches and whether the
run produces one video or two. Load `references/visuals.md` only if the answer is
yes.

#### 0.4 Resume

If `Videos Edited/<project>/master-plan.json` already exists, read it and ask
whether to continue from that cut or start fresh. Transcription is the expensive
step; never repeat it when `raw_transcript.json` is already present and the source
file's hash is unchanged.

### Phase 1: Research — build the record

No opinions in this phase. It produces facts.

```
python3 pipelines/video/ingest.py <project>     # pull, probe, extract audio, transcribe
python3 pipelines/video/takes.py <project>      # segment, find repeated lines
```

`ingest.py` pulls footage with rclone, sniffs each file before ffprobe sees it
(see `references/cut-rules.md`, untrusted media), extracts a mono 16kHz mp3, and
sends it to ElevenLabs Scribe **whole, in one request** — chunking splits words.
Writes `raw_transcript.json` with word-level timestamps.

`takes.py` segments on pauses and clusters repeated lines by **opening similarity**,
not whole-string similarity: a false start is a prefix of the real take, so a 6-word
abandoned start and its 114-word completion score low on overall similarity and high
on opening similarity.

If visuals are on, also gather candidate assets now — `references/visuals.md`.

### Phase 2: Plan — propose, then STOP

#### 2.1 Read the record and choose

Read the full utterance listing. For each cluster of repeated lines pick the keeper
and record why. **The algorithm under-detects and you are expected to catch what it
misses** — in particular, two tellings of the same beat that share almost no wording
are duplicates no string metric will connect, and a trailing fragment at the end of a
long kept segment will not appear as its own cluster.

Then choose transitions per join (`references/cut-rules.md`), caption phrasing
(`references/captions.md`), and B-roll placements if enabled.

#### 2.2 Write the plan and the transcript

```
python3 -m pipelines.video.plan <project>
```

Writes `master-plan.json` (spans with handles, joins, cut map) and
`final-transcript.txt` — exactly what the finished video will say.

#### 2.3 Adversarial review — required, before the gate

```
python3 -m pipelines.video.diff_check <project>
```

Then dispatch the **`reel-cut-adversary`** agent (`Agent` / `Task` in Claude Code,
`spawn_agent` in Codex) to review the cut against the original.

**Give it the artifacts, never your reasoning.** It reads `cut-review.json`,
`final-transcript.txt` and `takes.json` and works out for itself what was lost. An
agent handed your rationale returns it confirmed, which is precisely the failure
this step exists to prevent — a first pass of this cut dropped both mentions of the
secretary and rendered a video where a span opened on "she" with no referent. The
deterministic check reports `antecedent_candidates: []` for exactly that case.

Brief it with the project name and the paths, nothing more:

```
Adversarially review the proposed cut for project <project>.
Read data/video/<project>/cut-review.json (contains both full transcripts),
final-transcript.txt and takes.json. The cut should remove only redundancy —
repeated takes, false starts, stumbles. Every idea said once should survive.
There is no target length.

Check BOTH directions:
  over-cut  — unique content removed, references orphaned by a dropped span
  under-cut — a repeated take that survived, two spans telling the same beat
Report what was lost or what should have gone and did not.
```

**Every CONFIRMED finding must be resolved before the gate** — fix it, or carry it
into the call-outs with your reason for disagreeing. Never drop one silently.
PLAUSIBLE findings are judgement; say which you accepted.

Expect false positives on dangling references: the antecedent scan only sees
capitalised words, so a lowercase referent like "secretary" reads as missing. That
noise is deliberate — the check is complete rather than precise, and the agent
triages.

#### 2.4 THE TRANSCRIPT GATE — do not skip, do not render past it

**Send him `final-transcript.txt` and stop.** Reading it takes a minute and it has
caught real defects every time it has run: a missing antecedent, two abandoned
fragments, a duplicated clause. Rendering first wastes minutes and his attention.

Required gate output:

````text
Here's exactly what the cut will say — <N> words, <M:SS>.

[attach final-transcript.txt]

**Call outs:**
- [any unique content you propose removing, and why]
- [any take choice you are genuinely unsure about]

Approve and I'll render.
````

Omit the call-outs header when nothing survives. **Wait for his answer.** He will
often come back with removals; apply them and show the transcript again.

### Phase 3: Execute — render, verify, upload

```
python3 pipelines/video/render.py <project> [--visuals]
python3 pipelines/video/qc.py <project>
```

`render.py` validates first and **refuses to render on any failure** — a crossfade
longer than its handle, a B-roll window straddling a join, a missing asset. Then one
pass from the original source: cut, transitions, B-roll, captions. Never render onto
an already-encoded intermediate; that stacks generation loss.

`qc.py` re-transcribes the finished file cold and reports word count against plan,
whether each intended removal actually happened, plus blackdetect, freezedetect and
silencedetect. **Read the output. Do not upload on a surprise.**

#### 3.1 On-screen captions and descriptions

Write `titles-descriptions.txt` containing:

- **Four on-screen text captions** — the short text that sits *on the video* so a
  scroller stops. **Not** the Instagram caption. Length comes from the `topic`
  column of `Niyi_Scripts_Master_FULL.csv`: **7–60 characters, mostly 10–40**. His
  registers are all-caps and short (`CHATGPT SECRET CODES`) or title case with a
  parenthetical (`AI and Office Jobs Timeline (1–18 Months)`). Vary the hook pattern
  across the four, per `voice/HOOK_PATTERNS.md`. **A sentence is too long.**

  **Every caption must signal the subject.** 44 of his 46 past topics name AI,
  ChatGPT, tech or coding outright, and the other two clearly imply it. A pure
  curiosity gap with no subject — "SHE ASKED HIM TO LEAVE THE ROOM" — fails,
  because a scroller cannot tell they are entering AI content. Keep the intrigue,
  but anchor it: "SHE TRUSTED A 1965 CHATBOT".
- **Two descriptions** — full Instagram captions, each closing with a CTA built from
  `voice/CTA_PATTERNS.md`. These are meant to be long.
- **Hashtags** — every row of the master CSV carries a set.

Voice comes from `voice/STYLE_GUIDE.md`. Append image credits to both descriptions
when any asset required attribution. Suggest; never pick, never post.

#### 3.2 Upload

Everything goes to `Videos Edited/<project>/`. Report the Drive links.

#### 3.3 Report

State the runtime, what was removed, which transitions were used where, what QC
confirmed, **and anything you did not verify**.

## Hard rules

- **No fixed length.** Never propose cutting unique content to shorten a video.
- **Transitions:** `fadeblack` most of the time, `hblur` or `fade` occasionally,
  chosen per join with a recorded reason. No hard rule, no hard cuts.
- **Captions** are burned in, word-highlight style, bottom-anchored. Full spec in
  `references/captions.md`. They composite **above** B-roll.
- **Never upload without a readback.**
- **Never post to any platform.** This skill writes files to Drive and stops.

## Common pitfalls

- **Centring a caption block vertically.** It shifts every time a phrase wraps to two
  lines. Anchor the bottom edge; grow upward.
- **Defining spans at word boundaries.** Leaves no handle, so the crossfade eats the
  last syllable. Snap to words, then grow into the surrounding silence.
- **Trusting a keyword scan for B-roll.** "I read a paper" is an academic paper, not
  teletype paper. Placement is a reading task.
- **Previewing from a window that starts mid-word.** The preview lies and he will
  hear a problem that is not in the master. Start samples at a phrase boundary.
- **Treating a longer gap between takes as a bigger visual jump.** It does not
  correlate. Measure the frames.
