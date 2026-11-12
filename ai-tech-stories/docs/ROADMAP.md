# Roadmap and honest status

This project has architecture, creative standards, example episode artefacts and agent instructions. It does NOT yet have a functioning S3-to-video pipeline.

## Phase A: pilot storytelling
- [x] Independent creative project and agents
- [x] ELIZA research and first narration draft
- [x] Recording script can be freely improvised; storyboard deferred until after trimming
- [ ] Film and upload a pilot recording to private S3
- [ ] Review footage and agree what an excellent clean rough cut feels like

## Phase B: transcript-first editor
- [ ] Private S3 ingest, video/audio inventory and verified time mapping
- [ ] ElevenLabs Speech-to-Text/Scribe integration with word timestamp export
- [ ] Retake/false start detection, semantic alignment, and conservative EDL
- [ ] Produce clean presenter master from raw clips without destructive edits
- [ ] Recalculate kept speech into a clean, timestamped final transcript
- [ ] Test against genuine improvisation, repeated takes and factual corrections

## Phase C: automatic visual storytelling
- [ ] Generate a precise post-trim storyboard from the clean master
- [ ] Discover usable archives and validate provenance, licence and attribution
- [ ] Produce original diagrams and clearly marked AI reconstructions
- [ ] Assemble historical B-roll, captions, music and presenter footage deterministically
- [ ] Automated QA and final human review

## Phase D: repeatable batches
- [ ] Resumable jobs and S3 storage for intermediate/final artefacts
- [ ] Platform export presets and approval workflow
- [ ] Optimise for repeatable production of 20 episodes across two filming days

**Immediate next step:** shoot the ELIZA episode in the natural voice, including spontaneous observations. The first real file is the test fixture for building the media automation.
