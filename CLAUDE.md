# AI Pie Content Engine

This project is a weekly content idea and script generator for the AI Pie brand.
It scrapes trending topics from Reddit, Hacker News, YouTube, and Google Trends,
then generates ready-to-shoot video scripts in the creator's voice.

## How This Project Works

The pipeline runs as Claude Code agent skills:

1. `/discover-trends` -- Collects trending data from all sources (runs Python scripts)
2. `/score-topics` -- Ranks topics by velocity, engagement, relevance, novelty
3. `/extract-angles` -- Generates 4 content angles per topic (AGREE, DISAGREE, CONTRARIAN, PRACTICAL)
4. `/generate-scripts` -- Writes 60-second scripts in the creator's voice using RAG
5. `/build-voice-pack` -- Analyzes past scripts to build a style guide (run once)
6. `/weekly-batch` -- Runs the full pipeline end-to-end

## Key Directories

- `pipelines/` -- Python scripts for data collection, clustering, and retrieval
- `voice/samples/` -- Creator's 100+ past scripts (one .txt per file)
- `voice/` -- Generated style guide, hook patterns, CTA patterns
- `voice_db/` -- ChromaDB local vector store (auto-generated)
- `data/` -- Intermediate pipeline data (auto-generated)
- `outputs/` -- Final weekly scripts organized by week (auto-generated)

## Pipeline Data Flow

```
Ingest (Python) -> Cluster & Dedup (Python) -> Score (Claude reasons) -> Angles (Claude reasons) -> Scripts (Claude + RAG)
```

Python scripts handle deterministic work (API calls, embedding, clustering).
Claude Code handles reasoning work (scoring, angles, script writing).

## Script Structure

All generated scripts follow this structure:
- Hook (attention-grabbing first line)
- Journey Line (why this matters)
- Story (the core content)
- Reality Check (honest take / nuance)
- CTA (call to action)

Target length: 150-180 words (~60 seconds spoken).

## Conventions

- All pipeline data is JSON
- Dates use ISO 8601 format
- Weekly outputs go in `outputs/YYYY-WNN/`
- Reddit credentials are in environment variables, never hardcoded
- If a source fails (e.g., TikTok is down), continue with remaining sources
