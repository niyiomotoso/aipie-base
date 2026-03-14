# AI Pie Content Engine -- Implementation Plan

> Phased, end-to-end. Every phase ends with a test and a checkpoint with you.

---

## Phase 0: Project Setup & Dependencies
**Goal:** Get the project skeleton and all Python packages installed.

### Steps:
1. Initialize git repo in `aipie/`
2. Create the full folder structure (`.claude/skills/`, `pipelines/`, `voice/`, `data/`, `outputs/`)
3. Write `requirements.txt` with all free dependencies
4. Create a Python virtual environment and install everything
5. Write `CLAUDE.md` with operating instructions for Claude Code
6. Create all skill directories with placeholder `SKILL.md` files

### Test:
- [ ] `python -c "import praw, bertopic, chromadb, sentence_transformers, yt_dlp, pydantic; print('All good')"` passes
- [ ] Running `claude` in the `aipie/` folder loads `CLAUDE.md` correctly
- [ ] `/discover-trends` shows up as an available skill (even if it doesn't do anything yet)

### Checkpoint -- I'll need from you:
- Nothing yet. I can do this phase entirely.

---

## Phase 1: Data Collection -- Reddit ✅
**Goal:** Collect trending AI/tech/business posts from Reddit.

### Approach:
Uses Reddit's **public JSON endpoints** (no API key, no auth needed).
Reddit killed self-service API keys in Nov 2025 (Responsible Builder Policy),
so we append `.json` to subreddit URLs instead of using PRAW.

### Steps:
1. ✅ Write `pipelines/ingest_reddit.py` using public JSON endpoints:
   - Pull hot + top posts from target subreddits
   - Extract: title, selftext, score, upvote_ratio, comment count, URL, timestamp
   - Dedup by permalink, filter by age, sort by score
   - Save to `data/raw_reddit.json`
2. ✅ Define subreddit list (non-technical, general audience)
3. Wire up the `/discover-trends` skill to run this script (done in Phase 2+)

### Subreddits (non-technical, consumer-focused):
```
r/artificial, r/ChatGPT, r/OpenAI, r/singularity,
r/technology, r/startups, r/Entrepreneur, r/SaaS,
r/productivity, r/fintech, r/wallstreetbets
```

### Test:
- [x] `python pipelines/ingest_reddit.py` runs and saves real data to `data/raw_reddit.json`
- [x] JSON contains posts with title, score, num_comments, created timestamp
- [x] No auth errors, no rate limit errors
- [x] 1,446 unique posts collected from 11 subreddits

### Checkpoint:
- ✅ No credentials needed (public JSON endpoints)
- ✅ Subreddit list adjusted per user preference (non-technical audience)

---

## Phase 2: Data Collection -- Hacker News & YouTube ✅
**Goal:** Add two more reliable, free data sources.

### Steps:
1. ✅ Write `pipelines/ingest_hn.py`:
   - HN Firebase API (topstories, beststories, newstories)
   - Parallel fetching with ThreadPoolExecutor (20 workers)
   - 477 stories collected in test run
2. ✅ Write `pipelines/ingest_youtube.py`:
   - Uses yt-dlp search (no API key needed)
   - 8 search queries targeting AI tools, news, business, productivity
   - 110 unique videos collected in test run
3. Update `/discover-trends` skill to run all ingest scripts (Phase 9)

### Test:
- [x] `python pipelines/ingest_hn.py` saves real HN data (477 stories)
- [x] `python pipelines/ingest_youtube.py` saves real YouTube data (110 videos)
- [x] All three sources produce valid JSON

### Checkpoint:
- ✅ No credentials needed for either source
- ✅ YouTube uses trending search instead of specific channels (per user preference)

---

## Phase 3: Data Collection -- Google Trends ✅
**Goal:** Add Google Trends as a signal for what the general public is searching.

### Steps:
1. ✅ Write `pipelines/ingest_trends.py`:
   - Uses trendspyg RSS feeds (fast, no browser needed)
   - Pulls from 4 English-speaking regions (US, GB, CA, AU)
   - Deduplicates cross-region trends, merges geo info
   - 37 unique trends collected in test run
2. Skipped TikTok/Instagram/Facebook (not needed for now)

### Test:
- [x] `python pipelines/ingest_trends.py` saves Google Trends data (37 trends)
- [x] Trends include associated news articles for context

### Note:
Google Trends returns general daily trends (not tech-filtered). The clustering
phase (Phase 4) will cross-reference these with Reddit/HN/YouTube to surface
AI/tech-relevant ones. Tech topics do appear (e.g., "anthropic" was trending).

---

## Phase 4: Topic Clustering & Deduplication ✅
**Goal:** Merge data from all sources, remove duplicates, cluster into topics.

### Approach:
Uses BERTopic with tuned UMAP/HDBSCAN for initial clustering, then KMeans
sub-clustering to break apart oversized clusters (>50 items).

### Steps:
1. ✅ Write `pipelines/cluster_topics.py`:
   - Loads all raw data, normalizes into common schema
   - Embeds with sentence-transformers (all-MiniLM-L6-v2)
   - Clusters with BERTopic (UMAP n_components=10, HDBSCAN min_cluster_size=5)
   - Sub-clusters oversized topics with KMeans
   - Sorts by cross-source coverage + engagement
2. ✅ Each topic gets: keywords, representative title, source counts, engagement totals

### Results:
- 73 topic clusters from 2,070 input items
- 62 multi-source clusters, 16 with 3+ sources
- Cluster sizes: 5-114 items (median: 11)

### Checkpoint:
- ✅ Clusters look coherent (Anthropic/Pentagon, ChatGPT Atlas, AI tools, etc.)

---

## Phase 5: Trend Scoring & Ranking ✅
**Goal:** Score topics by velocity, engagement, relevance, and novelty.

### Steps:
1. ✅ Write `pipelines/score_topics.py`:
   - Velocity (0.30): cross-source coverage + volume (log scale)
   - Engagement (0.25): total engagement log-normalized against dataset max
   - Relevance (0.30): semantic similarity to 12 niche keyword phrases
   - Novelty (0.15): cluster size (smaller=more novel) + keyword specificity
2. ✅ Composite score with configurable weights
3. ✅ Relevance filter (default 0.25) drops off-niche topics (sports, celebrities)
4. ✅ Saves top N scored topics to `data/scored_topics.json`

### Results:
- 73 clusters -> 38 relevant topics (35 filtered as off-niche)
- Top 20 saved: AI tools, ChatGPT Atlas, Claude computer use, AI/SaaS, Anthropic/Pentagon, etc.

### Checkpoint:
- User to review top topics and confirm they're content-worthy (Phase 9 integration)

---

## Phase 6: Voice Pack & Script Style Engine ✅
**Goal:** Build the RAG system that learns Niyi's writing style from past scripts.

### Steps:
1. ✅ `pipelines/prep_voice_samples.py` — parsed CSV of 46 scripts into individual .txt files
2. ✅ `pipelines/index_voice.py` — embeds scripts, stores in ChromaDB, provides `query_similar()` function
3. ✅ Generated voice analysis files:
   - `voice/STYLE_GUIDE.md` — tone, language patterns, signature phrases, content themes
   - `voice/HOOK_PATTERNS.md` — 7 proven hook patterns with examples
   - `voice/CTA_PATTERNS.md` — 5 CTA patterns with formula

### Results:
- 46 scripts indexed in ChromaDB (voice_db/)
- Retrieval tested: "future of AI and jobs" → correctly returns "AI and Office Jobs Timeline"
- Style guide captures: conversational tone, direct address, analogy-based explanations, Nigerian cultural flavor
- User can add more scripts anytime and re-run to update

---

## Phase 7: Angle Generation & Scriptability Scoring
**Goal:** For each top topic, generate content angles and score how "scriptable" it is.

### Steps:
1. ✅ Updated `/extract-angles` skill:
   - Reads scored topics from `data/scored_topics.json`
   - **Web searches** each topic for current conversation context
   - Generates 4 angles: AGREE, DISAGREE, CONTRARIAN, PRACTICAL
   - Each angle includes: hook, thesis, emotion, risk level, key facts from research
   - Scores scriptability and filters below 0.6
   - Saves to `data/angles.json`
2. ✅ `pipelines/retrieve_similar.py` — helper for retrieving similar past scripts

### Test:
- [ ] `/extract-angles` produces 4 distinct angles per topic
- [ ] Angles include real facts from web research
- [ ] At least 5-7 topics pass the scriptability threshold

### Checkpoint -- I'll need from you:
- Review the angles. "Would you actually use any of these hooks?"

---

## Phase 8: Script Generation in Your Voice
**Goal:** Generate complete, ready-to-shoot scripts that sound like you.

### Steps:
1. ✅ Updated `/generate-scripts` skill:
   - Auto-loads voice guide, hook patterns, CTA patterns via dynamic context injection
   - Retrieves similar past scripts from ChromaDB via `retrieve_similar.py`
   - **Web searches** each topic for fresh facts and examples
   - Generates per topic: 3 hooks, full script (~150-200 words), caption, 3 comment prompts
   - Voice matching checklist built into the skill
   - Saves to `outputs/latest/scripts.json` and `outputs/latest/summary.md`

### Test:
- [ ] Generated scripts are ~150-200 words
- [ ] Scripts follow Hook → Journey Line → Story → Reality Check → CTA
- [ ] The tone matches Niyi's voice (conversational, direct, analogies, Nigerian flavor)
- [ ] Hooks are compelling and varied

### Checkpoint -- I'll need from you:
- **Read the generated scripts out loud.** Do they sound like you?
- Feedback on voice, hooks, CTAs — we iterate until you're happy

---

## Phase 9: Full Pipeline Integration (`/weekly-batch`)
**Goal:** Wire everything together into one command.

### Steps:
1. ✅ Updated `/weekly-batch` skill that orchestrates the full pipeline:
   - Step 1: Run all 4 ingest scripts (Reddit, HN, YouTube, Trends)
   - Step 2: `python pipelines/cluster_topics.py`
   - Step 3: `python pipelines/score_topics.py --top 20`
   - Step 4: Generate angles with web research (Claude reasoning)
   - Step 5: Generate scripts with RAG + web research (Claude reasoning)
   - Step 6: Save to `outputs/YYYY-WNN/`
   - Step 7: Present summary
2. Error handling built into each ingest script (continues if a source fails)

### Test:
- [ ] Type `/weekly-batch` in Claude Code
- [ ] Full pipeline runs end-to-end without errors
- [ ] Produces 5-7 complete scripts with hooks, captions, and comment prompts
- [ ] Takes a reasonable amount of time (target: under 10 minutes)
- [ ] Output folder `outputs/YYYY-WNN/` contains trends.json, scripts.json, summary.md

### Checkpoint -- I'll need from you:
- Run `/weekly-batch` and review the full output
- This is the "real world test" -- would you actually use these scripts this week?
- Final tuning: adjust scoring weights, voice guide, topic filters

---

## Phase 10 (Optional): GitHub + Automation
**Goal:** Set up version control and optional automated weekly runs.

### Steps:
1. Create a GitHub repo for the project
2. Set up `.gitignore` (exclude `voice_db/`, `data/`, API credentials)
3. Push code to GitHub
4. Set up GitHub Actions workflow for weekly cron:
   - Requires: Anthropic API key, Reddit credentials as GitHub Secrets
   - Pipeline runs every Monday at 6 AM
   - Results auto-committed to repo
5. (Optional) Add notification: Slack webhook / email when scripts are ready

### Test:
- [ ] Code is on GitHub, clean history
- [ ] GitHub Action triggers manually via `workflow_dispatch`
- [ ] Pipeline runs on GitHub's servers and produces outputs
- [ ] You get notified when scripts are ready

### Checkpoint -- I'll need from you:
- **GitHub repo name** (e.g., `aipie-content-engine`)
- **Anthropic API key** (from https://console.anthropic.com/) -- stored as GitHub Secret, never in code
- **Reddit credentials** -- stored as GitHub Secrets
- **(Optional) Slack webhook URL or email** for notifications

---

## Phase 11 (Optional): Refinement & Extras
**Goal:** Polish based on real-world usage.

### Possible additions (based on your feedback after using it for 2-3 weeks):
- Thumbnail idea generator skill
- Hook A/B testing skill (generate 5 hooks, help you pick)
- Performance tracker (log which scripts you actually used and how they performed)
- Topic blacklist (skip topics you've already covered)
- Weekly changelog (what changed in trending topics vs. last week)
- Script length variants (30s, 60s, 90s versions)

---

## Summary

| Phase | What | Depends On | You Provide |
|-------|------|------------|-------------|
| 0 | Project setup | Nothing | Nothing |
| 1 | Reddit ingestion | Phase 0 | Reddit account + app credentials |
| 2 | HN + YouTube ingestion | Phase 0 | List of YouTube channels to track |
| 3 | Google Trends + optional sources | Phase 0 | Trend keywords, optional TikTok/IG creds |
| 4 | Clustering & dedup | Phases 1-3 | Review clustered topics |
| 5 | Scoring & ranking | Phase 4 | Review ranked topics, adjust weights |
| 6 | Voice pack & RAG | Phase 0 | **Your 100+ past scripts** (most important) |
| 7 | Angles & scriptability | Phases 5+6 | Review angles, give feedback |
| 8 | Script generation | Phase 7 | Read scripts aloud, give voice feedback |
| 9 | Full pipeline integration | All above | Full end-to-end test |
| 10 | GitHub + automation | Phase 9 | GitHub repo, Anthropic API key |
| 11 | Refinements | Phase 9 | Feedback from real usage |

**Note:** Phase 6 (voice pack) can be done in parallel with Phases 1-5 once you provide your scripts. The sooner you gather them, the faster we move.

**Total estimated phases of work: 9 core + 2 optional.**
