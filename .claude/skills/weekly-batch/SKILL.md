---
name: weekly-batch
description: Run the full weekly content pipeline end-to-end. Collects trends, scores topics, generates angles, and writes scripts. Use this for your weekly content planning session.
disable-model-invocation: true
allowed-tools: Bash(python *), Read, Write, Glob, Grep
---

Run the complete weekly content pipeline.

## Pipeline Steps

### Step 1: Collect trending data
Run all ingest scripts. If any source fails, report the error but continue.
- `python pipelines/ingest_reddit.py`
- `python pipelines/ingest_hn.py`
- `python pipelines/ingest_youtube.py`
- `python pipelines/ingest_trends.py`

Report: how many posts collected from each source.

### Step 2: Cluster and deduplicate
- `python pipelines/cluster.py`

Report: how many unique topics found after dedup.

### Step 3: Score and rank topics
Read the clustered data and score each topic on:
- Velocity (0.35 weight)
- Engagement (0.25 weight)
- Relevance to AI/tech/finance (0.25 weight)
- Novelty (0.15 weight)

Save to `data/scored_topics.json`. Report top 10.

### Step 4: Generate angles
For the top 10 topics, generate 4 angles each (AGREE, DISAGREE, CONTRARIAN, PRACTICAL).
Score scriptability. Filter to topics scoring above 0.6.
Save to `data/angles.json`.

### Step 5: Generate scripts
Load voice guide: !`cat voice/STYLE_GUIDE.md 2>/dev/null || echo "No voice pack. Scripts will use default style."`
Run `python pipelines/retrieve_similar.py` if voice_db exists.

For the top 5-7 scriptable topics, generate:
- 3 hook options
- Full 60-second script (~150-180 words)
- Social media caption
- 3 comment prompts

### Step 6: Save outputs
Create output folder: `outputs/YYYY-WNN/` (current year and week number).
Also symlink or copy to `outputs/latest/`.
Save: `trends.json`, `scripts.json`, `summary.md`.

### Step 7: Present results
Show the summary: how many topics found, how many scripts generated, and list each script's topic + hook.
