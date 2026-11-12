# Roadmap and honest status

This initial commit creates architecture, creative guidelines, sample metadata, and agent instructions. It does not implement autonomous video editing.

## Phase A: establish the format
- [x] Separate project and first-draft production standards
- [x] Independent Claude Code and Codex instructions
- [x] Example episode, edit-plan and asset contracts
- [ ] Research, write and approve 2-5 pilot stories
- [ ] Record pilot footage and lock initial visual direction

## Phase B: build the automatic talking-head editor
- [ ] S3 ingest and encrypted, resumable local cache
- [ ] Word-timestamp transcription and confidence scoring
- [ ] Script/transcript alignment across paraphrases and retakes
- [ ] Non-destructive proposed cut list and approval interface/report
- [ ] FFmpeg rough-cut renderer, subtitle output and automated checks
- [ ] Validate against real recordings including mistakes and improvisations

## Phase C: visual storytelling engine
- [ ] Scene and B-roll beat planner grounded in actual narration
- [ ] Asset search, rights checking, downloading and provenance store
- [ ] AI illustration generator with disclosure/provenance
- [ ] Historical stills, video, graphics, crops and sound mix composition
- [ ] Visual QA and human review loop

## Phase D: batch production
- [ ] S3 render outputs and versioned approvals
- [ ] Queue of episode jobs with resumable failed stages
- [ ] Batch filming with parallel post-production
- [ ] Social export presets, captions and packaging
- [ ] Performance-informed feedback to the NEW storytelling guide

Build deterministic media components before trying to let an agent do everything in a single prompt. Test the quality of a complete episode before scaling to 20.
