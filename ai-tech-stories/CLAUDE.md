# Claude Code instructions: AI & Tech Stories

Work exclusively within this folder. This is a standalone storytelling project. Never look up, consume or reuse voice references, old scripts, prompt templates, pipelines, skills or databases from the parent repository. Develop the style from zero through discussion, experimentation and newly approved stories.

Read README.md, docs/CREATIVE_DIRECTION.md, docs/ARCHITECTURE.md and docs/ASSET_RIGHTS.md first.

Workflow skills:
- .claude/skills/develop-story/SKILL.md
- .claude/skills/assemble-video/SKILL.md

Story principles:
- First person when authentic, natural language, compelling tension and rigorous sourcing.
- Niyi's face and voice remain the centre of the story, with meaningful historical and technical visuals.
- Do not invent experiences, quotes, chronology or evidence.
- Do not turn the format into generic third-person documentary narration.
- **Filming script is not a verbatim requirement.** Allow personal improvisation and genuine anecdotes.

Video principles:
- **Never require Niyi to provide a manually rewritten final script after recording.**
- Original footage is the authoritative record of spoken words. Download from private S3, extract audio and prefer ElevenLabs speech-to-text with word timestamps.
- Preserve the raw transcript. Detect retakes, create a conservative EDL, and render a clean talking-head master with a matching timecoded transcript.
- Generate the final detailed storyboard AFTER cleaning the recording; pre-shoot visual notes are optional and non-binding.
- Agents propose editorial and timecoded creative plans; deterministic tools apply edits.
- Keep source footage immutable. Preserve meaningful pauses, authentic improvisations and natural personality.
- Suggest removal of repeated takes and false starts, but flag ambiguous edits for human review.
- Use the research dossier for factual QA, not to force filmed wording to match the script.
- Do not download or use visual assets without sufficient rights for the intended platforms.
- Clearly distinguish AI reconstructions from genuine archival footage.
- Human approval is required before publishing.

Write all changes and generated small metadata within this folder. Keep large media and credentials out of Git, in local ignored directories or private S3. Never claim automated editing is operational until verified using real footage.
