# Codex instructions: AI & Tech Stories

This project is an independent storytelling studio within ai-tech-stories/. Do not access any parent repository scripts, voice references, databases, templates or agents. Build a completely new narrative identity through approved story drafts.

Read README.md and the docs/ directory before proposing changes. Use:
- .agents/skills/develop-story/SKILL.md for source-backed story packages.
- .agents/skills/assemble-video/SKILL.md for footage-to-video plans.

The recording script is only a guide. Niyi may improvise, add a personal anecdote, or paraphrase. Do not request a manually updated final script. Instead, ingest immutable raw footage from private S3, use ElevenLabs word-timestamp transcription when available, choose coherent takes, and derive a clean master and cleaned transcript. Only then generate the detailed, timecoded visual storyboard.

Make modifications only inside this folder. Keep source footage immutable and out of Git. Distinguish creative editorial decisions from reproducible FFmpeg/media processing. Never silently remove words that affect meaning or authentic improvisation. Require provenance and licensing for external assets, clearly flag recreated visuals, and obtain human review before publishing.

Always state which automation functions actually exist and have been tested versus which are still proposed.
