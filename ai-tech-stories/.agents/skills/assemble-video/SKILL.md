---
name: assemble-video
description: Turn raw on-camera footage into a cleaned, accurate transcript-led story and then an AI/tech short documentary, preserving spontaneous additions.
---

# Assemble video: recorded performance is authoritative

Read `docs/ARCHITECTURE.md` and `docs/ASSET_RIGHTS.md` first. The skill defines the desired workflow; individual automation modules are not implemented until explicitly built and tested.

## NON-NEGOTIABLE: the filming script is NOT a verbatim transcript

Niyi may improvise, paraphrase, change order, expand an idea, include authentic personal experiences, add jokes, or omit scripted sentences. **This is normal and encouraged.** Never demand that Niyi rewrite, resubmit, or manually transcribe "the final script" after filming. Do not judge the recording as wrong merely because it differs from the script.

**Raw recordings + time-aligned speech transcript are the source of truth for what was spoken.** The approved research dossier and draft script remain useful context for checking factual claims and identifying intended narrative beats, but they do not override the recorded performance. Maintain the original transcript, edited transcript, source timecodes, and revised spoken-story text as generated artefacts.

Example: Niyi may spontaneously mention visiting the Computer History Museum in San Francisco after explaining early computers. Preserve this genuinely personal contribution if coherent and usable. Do not claim he saw the exact computer that ran ELIZA unless his recording and independent evidence establish that.

## The ordered, footage-first workflow

1. **Ingest immutable originals from private S3.** Retrieve video/audio with scoped credentials; hash files; inspect codecs, audio channels, sync, frame rate, and duration. No credentials or signed URLs in Git.
2. **Extract and time-map audio.** Use FFmpeg or another deterministic tool to extract a transcription copy (without changing source). Preserve source clip IDs, start offset and exact audio/video timestamp relationships.
3. **Transcribe via ElevenLabs.** Prefer the user's existing ElevenLabs Speech-to-Text/Scribe agent capability if available. Request word-level timestamps; enable speaker diarization only if beneficial. Keep `raw_transcript.json` with per-token times, confidence when provided, non-speech events and the complete verbatim text. Confirm the currently supported model/parameters against official docs before integration. If the ElevenLabs skill is unavailable, report the missing dependency or use an explicitly approved substitute. Never hallucinate a transcript.
4. **Identify takes and narrative continuity.** Segment at genuine pauses and repeated passages, locate false starts, complete retakes, accidental duplicates, misstatements and usable improvisations. Evaluate both semantics and visual/audio continuity. Do not use exact script matching as a deletion rule.
5. **Propose a conservative edit decision list (EDL).** Prefer complete coherent takes and remove clear abandoned/duplicate attempts. Keep personal anecdotes, meaning-bearing words, natural delivery and appropriate filler. Do not auto-cut every 'um', pause or breath. Mark ambiguous selections and possible factual inconsistencies for review.
6. **Render a CLEAN TALKING-HEAD ROUGH CUT first.** Apply non-destructive EDL to source footage; keep original clips intact. Produce `clean_master.mp4` and `clean_transcript.json`, recalculating timestamps into the rough cut using explicit source-to-output mapping. Confirm clean transcript against the audio after the cuts, not merely by concatenating text.
7. **Generate the detailed storyboard AFTER the rough cut.** Read the cleaned transcript and watch/analyse the actual performance. Build `storyboard.json` with exact output timestamps, purposeful returns to Niyi on camera, archival footage, custom diagrams, historical references, captions and sound cues. Any pre-recording visual notes are optional ideas only; never treat them as immutable scene instructions.
8. **Source or create assets from the approved storyboard.** Check rights and provenance before use. Record asset URLs, permitted uses, evidence and attribution. Clearly disclose/label fabricated illustrations and reconstructions where otherwise confusing. Never present an AI image as historical photographic evidence.
9. **Assemble and export.** Create a reproducible machine-readable timeline referencing the clean master, subtitle alignment and verified assets. Use deterministic media tooling (initially FFmpeg) for vertical framing, B-roll, captions, audio mix and `final_review.mp4`.
10. **Automated QA + editorial approval.** Check no speech is lost at cuts, words remain in order and meaning, audio is continuous, subtitles reflect the retained spoken content, rights are valid, visuals are accurate, text is mobile-safe and exports meet platform specs. Require Niyi's approval before publishing.

## Expected outputs (small metadata tracked in project; media stored privately)

- `raw_transcript.json`: untouched time-aligned transcription of original recordings.
- `selects.edl.json`: each retained section's original clip ID, in/out points, editorial rationale, confidence and review flag.
- `clean_transcript.json`: actual retained speech with new output timecodes and source references.
- `clean_master.mp4`: first render containing only the chosen on-camera narration, before B-roll.
- `storyboard.json`: precise post-trim scenes, shots, archival asset requests and timing.
- `assets.manifest.json`: sources, authenticity, usage rights and attribution for every selected asset.
- `final_review.mp4`: assembled version needing final sign-off.

If a module does not exist or has not been validated, state that clearly and create a scoped implementation task. The skill must not pretend a completed video exists.
