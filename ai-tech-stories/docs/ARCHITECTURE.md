# Autonomous post-production: footage-first architecture

## Core rule

**The approved recording script is a preparation document, not a verbatim specification for the final cut.** Niyi can improvise, paraphrase, change the order of a story, pause, add a genuine memory or add new comments. No manual "final script" submission is required after filming.

The recorded performance becomes the source of truth for the actual spoken story. The original research remains useful for checking spontaneous factual assertions. A final transcript, cut decisions and detailed storyboard are generated from the media itself.

## Pipeline

RESEARCH -> RECORDING SCRIPT -> FILM -> PRIVATE S3 UPLOAD -> AUDIO EXTRACTION -> ELEVENLABS TIMESTAMPED TRANSCRIPT -> RETAKE / CONTINUITY ANALYSIS -> EDIT DECISION LIST -> CLEAN TALKING-HEAD MASTER -> UPDATED TIMECODED TRANSCRIPT -> FINAL STORYBOARD -> RIGHTS-VERIFIED ASSETS / ILLUSTRATIONS -> AUTOMATED ASSEMBLY -> QA -> HUMAN SIGN-OFF

### Before filming: intentionally light

The creator needs only an approved spoken script. Research packs and lightweight visual feasibility notes may exist to prevent important historical claims or asset problems, but there is no need for a locked, timed storyboard. The script should invite natural improvisation and authentic anecdotes.

### After filming: S3 and immutable source files

The raw camera recording is uploaded to a private S3 path, for example `s3://<bucket>/aipie-stories/<id>/raw/`. Index the files by clip ID, SHA-256, camera/audio metadata and ingest date. Use private credentials and never commit video files or signed links to the public repo. Locally extract audio to a transcription format with a maintained mapping to original video timeline and any offset for separately recorded sound.

### Transcription: ElevenLabs is the preferred provider

Use the user's ElevenLabs skill when it is available to Claude Code or Codex, or implement a documented ElevenLabs Speech-to-Text/Scribe adapter. Request word-level timestamps so transcript words can be mapped to actual footage; diarization is optional for a single on-camera speaker. Preserve the full raw transcript including imperfect sentences, repeated attempts, filler and possible speech-recognition mistakes. Never make a speech recognition model rewrite the dialogue to match a pre-recording script.

Official docs at the time of design:
- https://elevenlabs.io/docs/overview/capabilities/speech-to-text
- https://elevenlabs.io/docs/api-reference/speech-to-text/convert

Model/version and supported parameters must be rechecked during implementation. ElevenLabs STT can accept video files too, but a deliberate audio-extraction stage preserves a clear A/V timing map and reduces transport complexity when appropriate.

### Select the best actual narration

Detect complete/abandoned takes, repetitions, changes of mind and silent gaps by analysing the raw transcript, acoustic timing and video frames. Prefer semantically coherent, complete takes. **Do not** interpret script deviations as mistakes. Personal additions such as the creator mentioning a visit to the Computer History Museum in San Francisco should be retained when they genuinely contribute to the story. If he is discussing technology from an era, do not automatically imply he viewed the specific historical machine mentioned in the story.

Generate a conservative, non-destructive EDL with source clip IDs and in/out seconds. Avoid cutting all filler words, breathing and natural pauses. Keep handles around cuts, avoid audible clicks and jarring jump cuts, and escalate uncertain choices or factual contradictions to a reviewer.

### Produce the clean master before the storyboard

Render a clean, intelligible talking-head video containing the selected narration only. Recalculate word timestamps into the **clean output's** clock using a source-to-output cut map and verify by re-listening or optional second-pass transcription. Generate a cleaned verbatim transcript. This transcript replaces the original recording script **for downstream timing and visual planning**, but doesn't overwrite it or the raw transcript.

### Dynamic storyboard

Only after the clean master is stable, generate the detailed storyboard. Ground each scene in the exact words, timing, pacing, expressions and narrative beats of the footage. For each beat choose whether to keep Niyi on screen or overlay archival material, original diagrams, historical documents or clearly marked AI reconstructions. Use original research to inform factual accuracy. Revisit the storyboard if the cut changes.

A pre-shoot visual idea list may still be helpful; it is never a requirement for filming and it is not a final timecoded storyboard.

### Asset collection and deterministic composition

Search for relevant visuals and retain licensing/provenance/attribution evidence. Only rights-verified assets go into output renders. Use AI-generated imagery for illustrative reconstructions with appropriate labels, never as fake archive evidence. Render a repeatable 9:16 timeline with FFmpeg or an equivalent compositor, speech-first audio, readable captions and scene placements derived from clean output timestamps.

### QA, review and hand-off

Verify audio continuity, omitted/duplicated speech, cleaned transcript accuracy, asset authenticity, commercial-platform rights, caption safe zones and export specs. Final human approval is required before publishing.

## Artifact contracts

- `raw_transcript.json`: words, start/end in original recording time, clip ID, confidence where available.
- `selects.edl.json`: chosen clip ranges with rationale, confidence and review flags.
- `clean_master.mp4`: edited presenter footage before B-roll, never overwriting original.
- `clean_transcript.json`: exactly what remains, timecoded to the clean master with source mapping.
- `storyboard.json`: scenes tied to clean master timestamps with purposeful visuals.
- `assets.manifest.json`: original/archival/generated status, rights evidence and attribution.
- `final_review.mp4`: full edited draft for creator sign-off.

Keep generated media and credentials out of Git. Agent reasoning can decide what to keep and how to illustrate it, while deterministic media tools perform timestamp-sensitive edits and re-renders.

## State of implementation

This document defines the intended system. S3 ingestion, ElevenLabs integration, shot/retake selection, renderers and QA must be developed and tested with real footage before the agent can automatically produce a finished video. Claude Code and Codex should both consume the same contracts, independently of any older voice/script pipelines elsewhere in the repo.
