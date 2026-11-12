# Autonomous post-production: proposed architecture

## Purpose

Given a source-backed approved script, real footage uploaded to private S3 and a creative brief, Claude Code or Codex should be able to prepare a professional short documentary edit with limited human supervision. The same pipeline should survive unscripted wording, natural improvisations, retakes and imperfect delivery.

## Pipeline

STORY DISCOVERY -> FACT-CHECKED SCRIPT -> VISUAL PRE-FLIGHT -> CAMERA RECORDING -> S3 INGEST -> TRANSCRIPTION + ALIGNMENT -> RETAKE ANALYSIS -> EDIT PLAN -> ASSET ACQUISITION / GENERATION -> TIMELINE COMPOSITION -> RENDER -> QA -> HUMAN APPROVAL

### 1. Editorial preparation

The script package contains a hook, source links, timeline, contested claims, narrative beats, on-camera recommendations, and visual suggestions. Approvals are recorded explicitly. Agents must not write shocking claims without attributable evidence.

### 2. Footage ingestion

Upload original camera and audio recordings to a private S3 prefix such as s3://<private-bucket>/aipie-stories/<episode-id>/raw/. A local worker or remote render node downloads with IAM credentials and verifies checksums. Never store presigned links, secrets or raw footage in the Git repository.

### 3. Transcription

Create word-level timestamped speech-to-text plus speaker labels (if needed), confidence scores and silence boundaries. Capture actual words spoken. Script-to-speech alignment is fuzzy and supports paraphrasing, skipped sentences and repeat takes. Keep the complete raw transcript.

### 4. Retake detection and edit decision list

Use acoustic pauses, transcript similarity, segment boundaries and repeated phrasing to propose preferred takes. Keep enough handles before and after cuts for natural transitions. Natural filler words can remain when they suit delivery. Never automatically delete wording that changes the argument. Low-confidence choices require a review flag.

### 5. Visual planning

Align actual approved narration (not just original script timestamps) to visual beats. Each beat can show camera, archival still, verified footage, diagram, graphical timeline or clearly designated AI reconstruction. Timing is data, not a hard-coded visual effect.

### 6. Asset acquisition

Search reputable archives and libraries, check rights BEFORE downloading into production, and record provenance, licence, permitted platforms and attribution. Use generators only for illustrative material and label reconstructions when they could otherwise be mistaken for evidence. Unknown rights fail closed.

### 7. Composition

An agent creates JSON edit and scene plans. Deterministic CLI/video tools assemble:
- Retained camera/audio segments
- On-camera/B-roll transitions and crops
- Historical still motion and simple diagrams
- Readable mobile subtitles
- Voice-first sound mixing and licensed music
- 9:16 platform-ready export and review proxy

FFmpeg is an initial rendering choice; other video compositors can be swapped in behind the same data contracts.

### 8. Quality assurance

Validate duration, resolution, audio continuity, clipping, scene gaps, caption safe zones, consistency between transcript and retained audio, asset licensing, misleading imagery and export format. Obtain editorial approval for final publish.

## Human checkpoints

Research sign-off; script voice sign-off; hard-to-source visual review; ambiguous retake choices; final-video approval. We can loosen low-risk gates only after successful real-world tests.

## Design decisions

- The project is intentionally independent, with no dependency on old scripts or the repository's existing content engine.
- Keep human-approved artefacts versioned. Raw recordings must remain unchanged.
- Separate LLM planning from deterministic media execution for auditability and re-renders.
- Avoid provider lock-in: Claude Code and Codex should both follow the project contracts.
- Run batch production only after a 2-5 episode quality pilot validates edit and review costs.
