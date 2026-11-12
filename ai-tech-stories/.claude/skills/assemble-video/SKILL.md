---
name: assemble-video
description: Plan and eventually assemble a first-person documentary edit from private S3 footage, timestamped transcripts and rights-verified visual assets.
---

# Assemble video

Read docs/ARCHITECTURE.md and docs/ASSET_RIGHTS.md. This is currently a workflow specification, not a functioning one-command rendering service.

1. Check that source footage is available via scoped private S3 access. Never put private URLs or credentials in Git.
2. Make an immutable copy of input metadata and inventory codecs, duration, audio tracks and checksums.
3. Transcribe actual speech with time alignment and confidence, then compare loosely against the approved script.
4. Detect possible retakes, repeated statements and abandoned starts. Present a proposed edit list with confidence and reasons.
5. Keep filler words by default unless they clearly harm clarity. Never remove natural personality or change meaning.
6. Obtain approval for uncertain cuts and save a structured, reproducible EDL.
7. Draft a visual beat plan tied to timestamps of the retained speech.
8. Acquire only assets whose commercial/social rights are verified; maintain complete attribution and authenticity metadata. Flag generated reconstructions.
9. Feed EDL and approved assets to deterministic tools for assembly, captions, sound and a review export.
10. Validate image truthfulness, source-to-speech alignment, audio sync, visual framing and licence status. Require final approval to publish.

If any tool does not exist yet, create a scoped implementation plan or implement/test it first. Do not hallucinate a completed video or claim the workflow already runs.
