---
name: generate-scripts
description: Generate ready-to-shoot 60-second video scripts in the creator's voice for top trending topics. Use after extract-angles has been run and voice pack exists.
allowed-tools: Bash(python *), Read, Write
---

Generate video scripts in the creator's voice.

## Context (loaded automatically)
- Voice guide: !`cat voice/STYLE_GUIDE.md 2>/dev/null || echo "Voice pack not built yet. Run /build-voice-pack first."`
- Hook patterns: !`cat voice/HOOK_PATTERNS.md 2>/dev/null || echo "No hook patterns yet."`
- CTA patterns: !`cat voice/CTA_PATTERNS.md 2>/dev/null || echo "No CTA patterns yet."`

## Instructions

1. Read `data/angles.json` for the scored topics and angles
2. Run `python pipelines/retrieve_similar.py` to get similar past scripts from ChromaDB
3. For each of the top 5-7 topics, using the best angle:

   Generate:
   - **3 hook options** (different opening lines)
   - **Full 60-second script** (~150-180 words) following: Hook -> Journey Line -> Story -> Reality Check -> CTA
   - **Social media caption** (platform-appropriate)
   - **3 comment prompts** (questions to drive engagement in comments)

4. Match the creator's voice from the style guide and example scripts
5. After writing each script, re-read it and check: does this sound like the creator or like generic AI?
6. Save all scripts to `outputs/latest/scripts.json`
7. Save a human-readable summary to `outputs/latest/summary.md`
8. Present the scripts for review
