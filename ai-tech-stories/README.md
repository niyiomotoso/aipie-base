# AI Pie: AI & Tech Stories

A NEW, self-contained project for researching, writing, recording and automatically editing highly engaging AI and technology stories.

This is deliberately not an extension of any existing content engine. Do not read or import scripts, templates, voice packs, skills, databases or content pipelines from elsewhere in the parent repository. The new storytelling voice will be developed from scratch through editorial experimentation and approved episodes.

## Vision

Create conversational, first-person short documentary stories about people, companies, nations, inventions, rivalries, unexpected consequences and technological breakthroughs. Niyi narrates on camera, supported by substantial historical archives, responsibly generated illustrations, graphics and sound.

The story must be fascinating on its own, not just a collection of facts. No artificial hype, no fabricated first-person memories, and no compulsory call to action.

## Production model

1. Discover and evaluate compelling story leads.
2. Research primary sources, verify claims and identify a specific narrative angle.
3. Develop a fresh storytelling voice with Niyi, then approve the recording script.
4. Plan visual beats and check that important assets are obtainable and usable.
5. Record on camera in batches. Upload original footage to private Amazon S3 storage.
6. Transcribe the footage with timestamps and locate false starts, repeated takes and improvisations.
7. Propose a non-destructive edit decision list for review.
8. Search, license or generate supporting visuals with provenance and clear reconstruction labels.
9. Assemble and render deterministically using media tools such as FFmpeg.
10. Review story accuracy, audio, visuals, rights and captions before publishing.

Claude Code and Codex should follow the same documented project contracts. Agent reasoning proposes editorial decisions; scripts and renderers execute reproducible operations.

## Folder map

- docs/CREATIVE_DIRECTION.md: creative identity, storytelling principles and decisions still to test.
- docs/ARCHITECTURE.md: envisioned media pipeline and data flow.
- docs/ASSET_RIGHTS.md: asset provenance and safe acquisition rules.
- docs/ROADMAP.md: realistic development milestones.
- templates/: example episode, edit and asset metadata contracts.
- episodes/: each episode's research, scripts and small metadata.
- tools/: future ingest, transcript alignment, render and QA tools.
- .claude/skills/: Claude Code workflows.
- .agents/skills/: Codex workflows.

## Status

This is a foundation and planning scaffold, not a finished video editor. Its skills currently describe the workflows and expected outputs; there is no implemented media ingest, transcription, licensed asset downloading or rendering yet. Building and testing those modules against actual footage is the next engineering phase.

All work on this series must remain inside ai-tech-stories/. Do not alter or depend upon the existing content project in the repository root.

IMPORTANT: Never commit source footage, rendered video, signed S3 URLs, API keys, downloaded copyrighted media or private credentials to this public repository.
