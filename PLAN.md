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

## Phase 1: Data Collection -- Reddit
**Goal:** Collect trending AI/tech/finance posts from Reddit.

### Steps:
1. Write `pipelines/ingest_reddit.py` that uses PRAW to:
   - Pull top 100 hot posts from target subreddits
   - Extract: title, body, score, comment count, URL, timestamp
   - Save to `data/raw_reddit.json`
2. Define the target subreddits list (AI/tech/finance focused)
3. Wire up the `/discover-trends` skill to run this script

### Default subreddits (we can adjust):
```
r/artificial, r/MachineLearning, r/OpenAI, r/ChatGPT, r/LocalLLaMA,
r/technology, r/programming, r/startups, r/singularity,
r/finance, r/fintech, r/wallstreetbets
```

### Test:
- [ ] `python pipelines/ingest_reddit.py` runs and saves real data to `data/raw_reddit.json`
- [ ] JSON contains posts with title, score, num_comments, created timestamp
- [ ] No auth errors, no rate limit errors

### Checkpoint -- I'll need from you:
- **Create a Reddit account** at https://www.reddit.com/register (if you don't have one)
- **Register a Reddit app** at https://www.reddit.com/prefs/apps:
  1. Click "create another app..."
  2. Name: `aipie-trends`
  3. Type: select "script"
  4. Redirect URI: `http://localhost:8080`
  5. Click "create app"
  6. Give me the **client_id** (string under the app name) and **client_secret**
- **Confirm or adjust the subreddit list** above

---

## Phase 2: Data Collection -- Hacker News & YouTube
**Goal:** Add two more reliable, free data sources.

### Steps:
1. Write `pipelines/ingest_hn.py`:
   - Hit HN Firebase API (`topstories.json`, `beststories.json`)
   - Pull top 200 stories with scores, comment counts, URLs
   - Save to `data/raw_hn.json`
2. Write `pipelines/ingest_youtube.py`:
   - Use yt-dlp to extract metadata from trending tech YouTube channels
   - Pull recent videos with view counts, like counts, titles
   - Save to `data/raw_youtube.json`
3. Update `/discover-trends` skill to run all three ingest scripts

### Test:
- [ ] `python pipelines/ingest_hn.py` saves real HN data
- [ ] `python pipelines/ingest_youtube.py` saves real YouTube data
- [ ] All three sources produce valid JSON with consistent schema

### Checkpoint -- I'll need from you:
- **A list of 5-10 YouTube channels** you follow for AI/tech content (so we scrape the right ones). Examples: MKBHD, Fireship, Two Minute Papers, AI Explained, etc. Give me channel names or URLs.

---

## Phase 3: Data Collection -- Google Trends + Optional Sources
**Goal:** Add Google Trends and optionally TikTok/Instagram/Facebook.

### Steps:
1. Write `pipelines/ingest_trends.py`:
   - Use trendspyg to pull trending searches for AI/tech/finance keywords
   - Save to `data/raw_trends.json`
2. (Optional) Write `pipelines/ingest_tiktok.py`:
   - Use TikTokApi to pull trending videos related to AI/tech
   - Requires your ms_token cookie
3. (Optional) Write `pipelines/ingest_instagram.py`:
   - Use Instaloader to pull from AI/tech hashtag feeds
   - Requires your Instagram login

### Test:
- [ ] `python pipelines/ingest_trends.py` saves Google Trends data
- [ ] (If enabled) TikTok and Instagram scripts produce data or gracefully fail
- [ ] All data files follow the same schema: title, text, score, source, timestamp

### Checkpoint -- I'll need from you:
- **Google Trends keywords** to track (defaults: "artificial intelligence", "AI tools", "ChatGPT", "tech layoffs", "fintech", "crypto"). Confirm or adjust.
- **(Optional) For TikTok:** Your `ms_token` cookie. To get it:
  1. Open TikTok in Chrome
  2. Open DevTools (Cmd+Option+I) > Application > Cookies
  3. Find the `ms_token` cookie and copy its value
- **(Optional) For Instagram:** Your Instagram username and password (used locally only, never stored in code)

---

## Phase 4: Topic Clustering & Deduplication
**Goal:** Merge data from all sources, remove duplicates, cluster into topics.

### Steps:
1. Write `pipelines/cluster.py`:
   - Load all `data/raw_*.json` files
   - Merge into unified format
   - Use sentence-transformers (`all-MiniLM-L6-v2`) to embed all titles+summaries
   - Deduplicate at 0.85 cosine similarity threshold
   - Run BERTopic clustering to group posts into topics
   - Save to `data/clustered_topics.json`
2. Each topic gets: representative title, source count, total engagement, list of sources

### Test:
- [ ] `python pipelines/cluster.py` runs without errors
- [ ] Obvious duplicates (same story from Reddit and HN) are merged
- [ ] Topics make sense (not random groupings)
- [ ] Output shows topic name, post count, total engagement, sources

### Checkpoint -- I'll need from you:
- Review the clustered output. I'll show you the top 20 topics and ask: "Do these make sense? Any weird groupings?"

---

## Phase 5: Trend Scoring & Ranking
**Goal:** Score topics by velocity, engagement, relevance, and novelty.

### Steps:
1. Add velocity scoring to `pipelines/cluster.py` or new `pipelines/score.py`:
   - Velocity: recent engagement vs. baseline (accelerating = high score)
   - Engagement: total upvotes + comments across sources
   - Relevance: cosine similarity to your niche keywords (AI, tech, finance)
   - Novelty: how different from previous weeks' topics
2. Composite score with configurable weights
3. Write `/score-topics` skill that runs scoring and presents ranked results
4. Save scored output to `data/scored_topics.json`

### Test:
- [ ] Top 10 topics are genuinely interesting and trending
- [ ] Topics that are clearly old news rank low
- [ ] Scoring weights produce sensible rankings
- [ ] Running `/score-topics` in Claude Code shows the ranked list

### Checkpoint -- I'll need from you:
- Review the top 10 ranked topics. Feedback: "Are these the kinds of things you'd actually want to make content about?"
- Adjust scoring weights if needed (e.g., "I care more about controversy than velocity")

---

## Phase 6: Voice Pack & Script Style Engine
**Goal:** Build the RAG system that learns your writing style from your past scripts.

### Steps:
1. Write `pipelines/index_voice.py`:
   - Read all scripts from `voice/samples/`
   - Chunk them into sections
   - Embed with sentence-transformers
   - Store in ChromaDB at `voice_db/`
2. Write `pipelines/retrieve_similar.py`:
   - Given a topic, query ChromaDB for the 5 most similar past scripts
   - Output the retrieved scripts as context
3. Write `/build-voice-pack` skill:
   - Claude Code reads your scripts and generates:
     - `voice/STYLE_GUIDE.md`
     - `voice/HOOK_PATTERNS.md`
     - `voice/CTA_PATTERNS.md`
4. Test retrieval: given a topic like "AI replacing jobs", does it retrieve your most relevant past scripts?

### Test:
- [ ] `python pipelines/index_voice.py` indexes all scripts into ChromaDB
- [ ] `python pipelines/retrieve_similar.py "AI replacing jobs"` returns 5 relevant scripts
- [ ] `/build-voice-pack` generates a style guide that accurately describes YOUR voice
- [ ] You read the style guide and say "yes, that sounds like me"

### Checkpoint -- I'll need from you:
- **Your 100+ past scripts** as text files in `voice/samples/`. Ideally:
  - One script per `.txt` file
  - Any naming convention is fine (e.g., `script_001.txt`, `ai_jobs.txt`, etc.)
  - If they're all in one document, give me the document and I'll split them
  - If they're in Notes/Notion/Google Docs, export them as text and drop them in the folder
- **This is the most important input for the entire project.** The quality of generated scripts depends directly on the quality and quantity of your sample scripts.

---

## Phase 7: Angle Generation & Scriptability Scoring
**Goal:** For each top topic, generate content angles and score how "scriptable" it is.

### Steps:
1. Write `/extract-angles` skill:
   - Claude Code reads scored topics from `data/scored_topics.json`
   - For each top topic, generates 4 angles: AGREE, DISAGREE, CONTRARIAN, PRACTICAL
   - Each angle includes: hook line, thesis, emotional appeal, risk level
   - Saves to `data/angles.json`
2. Add scriptability scoring:
   - Claude Code evaluates: emotional charge, controversy, practical takeaway, novelty, simplicity
   - Topics below threshold get filtered out

### Test:
- [ ] `/extract-angles` produces 4 distinct angles per topic
- [ ] Angles feel genuinely different (not just rephrased versions of each other)
- [ ] Scriptability scores make sense (complex topics score low on simplicity)
- [ ] At least 5-7 topics pass the scriptability threshold

### Checkpoint -- I'll need from you:
- Review the angles. "Would you actually use any of these hooks?"
- Feedback on angle quality: "Too generic? Too edgy? Not edgy enough?"

---

## Phase 8: Script Generation in Your Voice
**Goal:** Generate complete, ready-to-shoot scripts that sound like you.

### Steps:
1. Write `/generate-scripts` skill:
   - Loads voice guide, hook patterns, CTA patterns
   - Retrieves similar past scripts from ChromaDB
   - For each top topic + best angle, generates:
     - 3 hook options
     - Full 60-second script (~150-180 words)
     - Caption for social media
     - 3 comment prompts to drive engagement
   - Saves to `outputs/latest/scripts.json` and `outputs/latest/summary.md`
2. Include a tone-check pass: Claude Code re-reads the generated script and checks if it matches your voice guide

### Test:
- [ ] Generated scripts are ~150-180 words (60-second read)
- [ ] Scripts follow your Hook → Journey Line → Story → Reality Check → CTA structure
- [ ] The tone matches YOUR voice (not generic AI voice)
- [ ] Hooks are compelling and varied across topics
- [ ] Captions are platform-appropriate

### Checkpoint -- I'll need from you:
- **Read the generated scripts out loud.** Do they sound like you? This is the critical test.
- Feedback: "This one sounds like me / This one is too formal / This hook is fire / This CTA is weak"
- We iterate on the voice guide and prompt until you're happy

---

## Phase 9: Full Pipeline Integration (`/weekly-batch`)
**Goal:** Wire everything together into one command.

### Steps:
1. Write `/weekly-batch` skill that orchestrates the full pipeline:
   - Step 1: Run all ingest scripts (Reddit, HN, YouTube, Trends, optional sources)
   - Step 2: Cluster and deduplicate
   - Step 3: Score and rank topics
   - Step 4: Generate angles for top 10
   - Step 5: Filter by scriptability (keep top 5-7)
   - Step 6: Generate scripts in your voice
   - Step 7: Save everything to `outputs/YYYY-WNN/`
   - Step 8: Show you a summary of what was produced
2. Add error handling: if one source fails (e.g., TikTok is down), continue with the rest
3. Add progress reporting: Claude Code tells you what step it's on

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
