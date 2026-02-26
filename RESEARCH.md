# AI Pie Content Engine - Full Research Report

> Compiled Feb 26, 2026 | Sources: Anthropic docs, GitHub repos, PyPI, web research
> Updated: Removed all paid services. Everything is 100% free (except your existing Claude Code usage).

---

## How This Works (No Servers, No Extra Costs)

**Everything runs locally on your Mac through Claude Code.**

- You open Claude Code in the `aipie/` folder
- You type `/weekly-batch` (or individual skills like `/discover-trends`)
- Claude Code runs the Python scripts to collect data from free sources
- Claude Code ITSELF does the reasoning (scoring, angles, script writing) -- no separate API key needed
- Results are saved as files on your Mac

**What you DON'T need:**
- No servers or cloud hosting (ChromaDB runs as local files on your Mac)
- No GitHub account (optional, only if you want version control or automated scheduling)
- No separate Anthropic API key (Claude Code IS the LLM engine)
- No paid APIs (everything uses free, open-source tools)

**What you DO need:**
- Your Mac
- Claude Code (which you already have)
- Free API credentials for Reddit (takes 2 minutes to register)
- Python 3.12+ installed

---

## Table of Contents

1. [Claude Code Agent Skills Architecture](#1-claude-code-agent-skills-architecture)
2. [Social Media Scraping Tools & Free APIs](#2-social-media-scraping-tools--free-apis)
3. [Trend Detection & Topic Clustering](#3-trend-detection--topic-clustering)
4. [RAG for Voice/Style Matching](#4-rag-for-voicestyle-matching)
5. [Content Scoring & Angle Generation](#5-content-scoring--angle-generation)
6. [Automation & Scheduling](#6-automation--scheduling)
7. [Recommended Tech Stack](#7-recommended-tech-stack)
8. [Proposed Project Structure](#8-proposed-project-structure)

---

## 1. Claude Code Agent Skills Architecture

### What Are Skills?

Skills are **markdown files with YAML frontmatter** that add modular capabilities to Claude Code. Each skill is a directory containing a `SKILL.md` file and optional supporting files (scripts, templates, examples).

### Where Skills Live

| Scope | Path | Who Uses It |
|-------|------|-------------|
| Personal | `~/.claude/skills/<skill-name>/SKILL.md` | You, across all projects |
| Project | `.claude/skills/<skill-name>/SKILL.md` | This project only |

### SKILL.md Format

```yaml
---
name: discover-trends
description: Scrape Reddit, HN, and other sources for trending AI/tech topics from the past 7 days.
argument-hint: "[days] [topic-filter]"
allowed-tools: Bash(python *), Read, Grep
---

Run the trend discovery pipeline:
1. Execute `python pipelines/ingest_reddit.py`
2. Execute `python pipelines/ingest_hn.py`
3. Read the output in `data/raw_trends.json`
4. Summarize the top 20 trending topics
```

### Key Frontmatter Fields

| Field | Purpose |
|-------|---------|
| `name` | Slash command name (e.g., `/discover-trends`) |
| `description` | Claude uses this to decide when to auto-load the skill |
| `argument-hint` | Shown during autocomplete |
| `disable-model-invocation` | Set `true` for skills with side effects |
| `allowed-tools` | Tools Claude can use without asking permission |
| `context: fork` | Run in isolated subagent context |
| `agent` | Subagent type: `Explore`, `Plan`, `general-purpose` |

### Dynamic Context Injection

Shell commands run BEFORE the prompt reaches Claude using `` !`command` `` syntax:

```yaml
---
name: weekly-report
---
Current week data: !`cat outputs/latest/trends.json`
Voice guide: !`cat voice/STYLE_GUIDE.md`

Generate this week's content scripts...
```

### How Skills Chain Together

Skills don't directly call each other. Instead:
1. **Claude's automatic composition** -- Claude loads multiple relevant skills based on descriptions
2. **Subagent chaining** -- One skill runs in `context: fork`, returns results, Claude uses those for the next step
3. **Hooks** -- `PostToolUse` and `Stop` hooks can enforce quality gates between steps

### CLAUDE.md (Operating Instructions)

CLAUDE.md is auto-loaded at session start. Use it for:
- Project-wide rules and conventions
- Frequently used commands
- Pipeline execution instructions
- References to skills and their order

Supports `@path/to/import` for importing additional files. Also supports modular rules in `.claude/rules/*.md` with path-specific YAML frontmatter.

### MCP Servers

MCP (Model Context Protocol) extends Claude Code with external tools/APIs:
```bash
# Add a local MCP server
claude mcp add --transport stdio my-tool -- python my_mcp_server.py
```

Project-scoped MCP config goes in `.mcp.json` at project root.

---

## 2. Social Media Scraping Tools & Free APIs

### Reliability Ranking (Best to Worst)

1. **Hacker News** -- Free, no auth, no rate limits, stable API
2. **YouTube** -- yt-dlp (no auth) + official API (10K units/day free)
3. **Reddit** -- PRAW is mature and reliable, free for non-commercial
4. **Product Hunt** -- GraphQL API, free to register
5. **Google Trends** -- Use trendspyg (pytrends is DEAD/archived)
6. **TikTok** -- TikTokApi works but fragile, needs cookie management
7. **Instagram** -- Instaloader works but most fragile, expect breakage
8. **Facebook** -- Hardest platform, no reliable free solution

### Reddit

**PRAW (Python Reddit API Wrapper)** -- RECOMMENDED
- Install: `pip install praw`
- Version: 7.8.1 (Nov 2025) -- actively maintained
- Auth: OAuth2 (free to obtain at reddit.com/prefs/apps)
- Rate limit: 100 QPM (auto-handled by PRAW)
- Data: Posts, comments, scores, subreddit listings (hot/new/top/rising)
- Async version: `pip install asyncpraw`

```python
import praw

reddit = praw.Reddit(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    user_agent="aipie-trends/1.0"
)

for post in reddit.subreddit("artificial").hot(limit=100):
    print(post.title, post.score, post.num_comments)
```

**YARS (no API key needed)** -- BACKUP
- Install: `pip install yars`
- Uses Reddit's public `.json` endpoints
- No auth required, but less reliable

### Hacker News

**Official Firebase API** -- BEST SOURCE
- Base URL: `https://hacker-news.firebaseio.com/v0/`
- Auth: None
- Rate limits: None
- Endpoints:
  - `/v0/topstories.json` -- Top 500 story IDs
  - `/v0/newstories.json` -- Newest 500
  - `/v0/beststories.json` -- Best 500
  - `/v0/item/<id>.json` -- Individual item

**Algolia HN Search API** -- FOR SEARCH
- URL: `https://hn.algolia.com/api/v1/search?query=<query>`
- GitHub repo archived Feb 10, 2026, but API still works
- Python wrapper: `pip install python-hn`

### YouTube

**yt-dlp** -- FOR METADATA (NO AUTH)
- Install: `pip install yt-dlp`
- Version: 2026.02.21 (extremely actively maintained)
- No auth needed for public content
- Data: title, description, view count, like count, comment count, tags, categories

```bash
yt-dlp --dump-json "https://www.youtube.com/watch?v=VIDEO_ID"
```

**YouTube Data API v3** -- FOR STRUCTURED QUERIES
- Auth: API key (free via Google Cloud Console)
- Free tier: 10,000 units/day
- Trending: `GET /youtube/v3/videos?chart=mostPopular` (1 unit)
- Search: 100 units per request (expensive -- only 100 searches/day)

### Google Trends

**trendspyg** -- RECOMMENDED (pytrends is DEAD)
- Install: `pip install trendspyg`
- pytrends was archived April 17, 2025 -- do NOT use
- Alternative: `pip install pytrends-modern` (async, type hints)
- Google's official Trends API launched July 2025 but is alpha-only (must apply)

### TikTok

**TikTokApi** -- BEST OPTION (fragile)
- Install: `pip install TikTokApi && python -m playwright install`
- Version: 7.2.2 (Feb 2026) -- actively maintained
- Requires `ms_token` cookie from your TikTok browser session
- Data: trending videos, user info, hashtags, video metadata

```python
from TikTokApi import TikTokApi
import asyncio, os

ms_token = os.environ.get("ms_token")

async def trending():
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3)
        async for video in api.trending.videos(count=30):
            print(video.as_dict)

asyncio.run(trending())
```

**yt-dlp for TikTok** -- BACKUP (individual videos/users)
```bash
yt-dlp --dump-json "https://www.tiktok.com/@username/video/123"
```

### Instagram

**Instaloader** -- BEST OPTION (fragile)
- Install: `pip install instaloader`
- Version: 4.15 (Nov 2025)
- Login recommended to avoid 401 errors
- Data: posts, captions, comments, likes, hashtags, stories, metadata
- Residential proxies recommended

```bash
instaloader profile <username>
instaloader "#trending"
instaloader --login=your_username profile target_user
```

### Facebook

**facebook-pages-scraper** -- BEST AVAILABLE
- Install: `pip install facebook-pages-scraper`
- Released: Oct 2025
- No webdriver or API key needed
- Data: page name, likes, followers, engagement stats
- Limited compared to other platforms

**facebook-scraper (kevinzg)** -- BACKUP
- Install: `pip install facebook-scraper`
- Still alpha, unreliable in 2026
- Cookies recommended

### Product Hunt

**Product Hunt API v2 (GraphQL)**
- Endpoint: `https://api.producthunt.com/v2/api/graphql`
- Auth: OAuth2 token (free to register)
- Rate: 6,250 complexity points per 15 min
- Data: products, votes, comments, collections, topics

---

## 3. Trend Detection & Topic Clustering

### BERTopic -- RECOMMENDED for Topic Clustering

```bash
pip install bertopic
```

Pipeline: Sentence-Transformers (embed) -> UMAP (reduce dims) -> HDBSCAN (cluster) -> c-TF-IDF (topic words)

```python
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
topic_model = BERTopic(embedding_model=embedding_model)
topics, probs = topic_model.fit_transform(documents)
topic_model.get_topic_info()
```

**Dynamic topics over time** (critical for weekly trend detection):
```python
topics_over_time = topic_model.topics_over_time(
    docs=documents,
    timestamps=timestamps,
    nr_bins=20
)
```

### BERTrend -- PURPOSE-BUILT for Emerging Trends

```bash
pip install bertrend
```
- Classifies signals as: Noise, Weak Signal (early indicators), Strong Signal (widely covered)
- Built on top of BERTopic
- Requires Python >= 3.12, GPU with 16GB RAM recommended
- Includes LLM-based signal interpretation

### Velocity Scoring (How Fast a Topic Is Rising)

```python
def compute_velocity(topic_posts, window_days=7):
    """Velocity = ratio of recent engagement to baseline."""
    now = datetime.now()
    recent = [p for p in topic_posts if (now - p['created']).days <= 3]
    baseline = [p for p in topic_posts if 3 < (now - p['created']).days <= window_days]

    recent_avg = sum(p['engagement'] for p in recent) / max(len(recent), 1)
    baseline_avg = sum(p['engagement'] for p in baseline) / max(len(baseline), 1)

    velocity = recent_avg / max(baseline_avg, 1)
    return velocity  # >1 = accelerating, <1 = decelerating
```

### Deduplication Across Sources

Use cosine similarity on embeddings to merge near-identical stories from Reddit, HN, YouTube, etc.:

```python
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")

def deduplicate(posts, threshold=0.85):
    texts = [p['title'] + " " + p.get('text', '')[:200] for p in posts]
    embeddings = model.encode(texts, convert_to_tensor=True)
    cos_scores = util.cos_sim(embeddings, embeddings)

    clusters = []
    used = set()
    for i in range(len(posts)):
        if i in used:
            continue
        cluster = [i]
        for j in range(i+1, len(posts)):
            if j not in used and cos_scores[i][j] > threshold:
                cluster.append(j)
                used.add(j)
        used.add(i)
        clusters.append(cluster)

    # Merge clusters: keep highest engagement post as representative
    deduped = []
    for cluster in clusters:
        best = max(cluster, key=lambda idx: posts[idx].get('engagement', 0))
        merged = posts[best].copy()
        merged['source_count'] = len(cluster)
        merged['sources'] = [posts[idx]['source'] for idx in cluster]
        deduped.append(merged)

    return deduped
```

### Extracting Debate Points from Comments

Claude Code itself handles this reasoning. In the skill prompt, you simply instruct:

```
Read the comments data from data/comments.json.
For each topic, extract:
1. Main points people AGREE on
2. Main points people DISAGREE about
3. Most controversial sub-topics
4. Contrarian or unexpected positions
Save the analysis to data/debate_points.json
```

No separate API calls needed -- Claude Code IS the LLM doing this analysis.

---

## 4. RAG for Voice/Style Matching

### Architecture

```
[100+ Past Scripts] -> [Chunk & Embed] -> [ChromaDB Vector Store]
                                                    |
[Trending Topic] -> [Query Embedding] -> [Similarity Search] -> [Top 3-5 Scripts]
                                                                        |
                                            [Claude + Voice Guide + Retrieved Scripts]
                                                                        |
                                                                [New Script in Your Voice]
```

### Step 1: Build Voice Pack (Run Once via `/build-voice-pack`)

When you run `/build-voice-pack`, Claude Code reads your scripts from `voice/samples/` and generates:

- `voice/STYLE_GUIDE.md` -- tone, vocabulary, rhythm patterns
- `voice/HOOK_PATTERNS.md` -- your opening formulas
- `voice/CTA_PATTERNS.md` -- your closing patterns

Claude Code does this analysis itself -- no separate API needed. The skill prompt instructs Claude to read the sample scripts and extract style characteristics.

### Step 2: Index Scripts in ChromaDB

```bash
pip install chromadb sentence-transformers
```

```python
import chromadb

chroma_client = chromadb.PersistentClient(path="./voice_db")
collection = chroma_client.get_or_create_collection(
    name="creator_scripts",
    metadata={"hnsw:space": "cosine"}
)

def index_scripts(scripts):
    for i, script in enumerate(scripts):
        collection.add(
            documents=[script['text']],
            metadatas=[{'title': script.get('title', ''), 'topic': script.get('topic', '')}],
            ids=[f"script_{i}"]
        )
```

### Step 3: Generate Scripts Using RAG (via `/generate-scripts`)

The `/generate-scripts` skill works like this:
1. A Python script queries ChromaDB for the 5 most similar past scripts to the current topic
2. The skill uses dynamic context injection to load the voice guide and retrieved scripts
3. Claude Code reads everything and writes the new script in your voice

The skill prompt uses `!`command`` to inject context:

```yaml
---
name: generate-scripts
description: Generate video scripts in your voice for scored topics
allowed-tools: Bash(python *), Read, Write
---

Voice guide: !`cat voice/STYLE_GUIDE.md`
Hook patterns: !`cat voice/HOOK_PATTERNS.md`
Similar past scripts: !`python pipelines/retrieve_similar.py`
Scored topics: !`cat data/scored_topics.json`

For each topic in scored_topics.json:
1. Write a 60-second script (~150-180 words) matching my voice
2. Include a strong hook (use patterns from HOOK_PATTERNS.md)
3. End with a clear CTA
4. Provide 3 hook options per script
5. Save all scripts to outputs/latest/scripts.json
```

No separate API calls -- Claude Code itself writes the scripts.

### Vector Store Comparison

| Feature | ChromaDB | LanceDB | FAISS |
|---------|----------|---------|-------|
| Install | `pip install chromadb` | `pip install lancedb` | `pip install faiss-cpu` |
| Persistence | Built-in disk | Disk-native (Arrow) | Manual save/load |
| Metadata filter | Yes | Yes | No |
| Best for | Prototyping | Production | Raw speed |
| **Recommendation** | **Start here** | Graduate later | Only if needed |

### Embedding Models (All Free, Run Locally)

| Model | Dims | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| `all-MiniLM-L6-v2` | 384 | Very fast | Good | Clustering, dedup, RAG |
| `all-mpnet-base-v2` | 768 | Medium | Better | Higher accuracy if needed |

> Note: Voyage AI (`voyage-2`) was removed -- it's a paid API. The local models above are more than sufficient for 100+ scripts.

---

## 5. Content Scoring & Angle Generation

### Scriptability Scoring

```python
from pydantic import BaseModel

class ScriptabilityScore(BaseModel):
    emotional_charge: float       # 0-1
    controversy: float            # 0-1
    practical_takeaway: float     # 0-1
    novelty: float                # 0-1
    simplicity: float             # 0-1
    visual_potential: float       # 0-1
    overall: float                # Weighted composite

# Use Claude structured outputs for guaranteed valid JSON
response = client.messages.parse(
    model="claude-sonnet-4-5-20250514",
    max_tokens=1000,
    output_format=ScriptabilityScore,
    messages=[{"role": "user", "content": f"Score this topic: {topic}"}]
)
score = response.parsed_output  # Guaranteed valid ScriptabilityScore
```

### Angle Generation

```python
class ContentAngle(BaseModel):
    angle_type: str        # "agree", "disagree", "contrarian", "practical"
    hook: str              # First sentence
    thesis: str            # Core argument
    emotional_appeal: str  # Target emotion
    risk_level: str        # "safe", "moderate", "spicy"
```

Generate 4 angles per topic: AGREE, DISAGREE, CONTRARIAN, PRACTICAL.

### Virality Research Findings

- **Moral-emotional language** increases virality
- **Sentiment intensity** matters more than just positive/negative
- **Novelty vs. prior content** can be quantified with embedding similarity
- AI-generated scripts matching successful patterns see up to **60% higher engagement**

---

## 6. How You'll Use It (No Automation Needed for MVP)

### Your Weekly Workflow

1. Open terminal in `aipie/` folder
2. Run `claude` to start Claude Code
3. Type `/weekly-batch` -- Claude Code does everything:
   - Collects trending data from Reddit, HN, YouTube, Google Trends
   - Clusters and deduplicates topics
   - Scores them for velocity and scriptability
   - Generates 5-7 scripts in your voice
   - Saves everything to `outputs/latest/`
4. Review the scripts, pick the ones you like, shoot your content

That's it. No servers, no cron jobs, no GitHub.

### Output Storage (Local Folders)

```
outputs/
  2026-W09/
    trends.json           # Raw scored topics
    scored_topics.json    # Filtered by threshold
    scripts.json          # Generated scripts
    summary.md            # Human-readable report
  2026-W10/
    ...
```

### Future Automation (Optional, For Later)

If you eventually want it to run automatically every Monday without you opening Claude Code, you'd need:
- A GitHub repo + GitHub Actions (free cron scheduling)
- An Anthropic API key (for programmatic Claude calls from Python)
- Not needed for the MVP, but documented below for when you're ready

### GitHub Actions (Free Weekly Cron)

```yaml
# .github/workflows/weekly-trends.yml
name: Weekly Trend Pipeline
on:
  schedule:
    - cron: '0 6 * * 1'  # Every Monday 6AM UTC
  workflow_dispatch:       # Manual trigger

jobs:
  detect-trends:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12', cache: 'pip' }
      - run: pip install -r requirements.txt
      - run: python pipeline/run_weekly.py
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          REDDIT_CLIENT_ID: ${{ secrets.REDDIT_CLIENT_ID }}
          REDDIT_CLIENT_SECRET: ${{ secrets.REDDIT_CLIENT_SECRET }}
      - run: |
          git config user.name "Trend Bot"
          git config user.email "bot@aipie.com"
          git add outputs/
          git diff --staged --quiet || git commit -m "Weekly trends: $(date +%Y-%m-%d)"
          git push
```

### Why GitHub (Clarification)

GitHub serves two purposes in this project:
1. **Version control** -- track changes to your code and outputs over time (git history). You can also use local git without GitHub.
2. **GitHub Actions** -- free automated cron jobs that can run the pipeline every Monday without you doing anything. This is the ONLY reason you'd need GitHub hosting specifically.

For the MVP, you don't need GitHub at all. You run everything locally through Claude Code.

### Why Anthropic API Key (Clarification)

- **Claude Code** (what you use) = the CLI tool. When you type `/weekly-batch`, Claude Code IS the LLM that does the reasoning. You're already paying for this through your existing subscription.
- **Anthropic API key** = only needed if Python scripts need to call Claude programmatically (e.g., for the GitHub Actions automation above, where Claude Code isn't in the loop).
- For the MVP, you don't need a separate API key. Claude Code handles all LLM reasoning.

---

## 7. Recommended Tech Stack

**Everything below is 100% free and runs locally on your Mac.**

### MVP (Core -- All Free)

| Component | Tool | Install | Cost |
|-----------|------|---------|------|
| **LLM Engine** | Claude Code (you already have this) | -- | Existing subscription |
| **Topic clustering** | BERTopic | `pip install bertopic` | Free |
| **Embeddings** | all-MiniLM-L6-v2 | `pip install sentence-transformers` | Free (local) |
| **Vector store** | ChromaDB | `pip install chromadb` | Free (local files) |
| **Reddit** | PRAW | `pip install praw` | Free (OAuth, 2 min to register) |
| **Hacker News** | Firebase API | `requests` | Free (no auth needed) |
| **YouTube metadata** | yt-dlp | `pip install yt-dlp` | Free (no auth needed) |
| **Google Trends** | trendspyg | `pip install trendspyg` | Free |
| **Deduplication** | sentence-transformers | already installed | Free |
| **Structured data** | Pydantic | `pip install pydantic` | Free |

### Optional (Best-Effort Sources -- All Free)

| Component | Tool | Install | Cost |
|-----------|------|---------|------|
| **TikTok** | TikTokApi | `pip install TikTokApi` | Free (needs ms_token cookie) |
| **Instagram** | Instaloader | `pip install instaloader` | Free (login recommended) |
| **Facebook** | facebook-pages-scraper | `pip install facebook-pages-scraper` | Free |
| **Product Hunt** | API v2 (GraphQL) | HTTP requests | Free (OAuth, 2 min to register) |

### Future (For Automation -- Only When Needed)

| Component | Tool | Cost |
|-----------|------|------|
| **Version control** | GitHub | Free |
| **Automated scheduling** | GitHub Actions | Free (2000 min/month on private repos) |
| **Programmatic LLM calls** | Anthropic API key | Paid per token |

### Full requirements.txt

```
praw>=7.8.0
bertopic>=0.16.0
sentence-transformers>=3.0.0
chromadb>=0.5.0
yt-dlp>=2026.1.0
trendspyg>=1.0.0
pydantic>=2.0.0
requests>=2.31.0
# Optional sources
TikTokApi>=7.2.0
instaloader>=4.15
facebook-pages-scraper>=1.0.0
```

---

## 8. Proposed Project Structure

```
aipie/
  CLAUDE.md                              # Operating instructions for Claude Code
  requirements.txt                       # Python dependencies

  .claude/
    skills/
      discover-trends/
        SKILL.md                         # /discover-trends -- collects data from all sources
      score-topics/
        SKILL.md                         # /score-topics -- ranks by velocity & scriptability
      extract-angles/
        SKILL.md                         # /extract-angles -- generates content angles
      generate-scripts/
        SKILL.md                         # /generate-scripts -- writes scripts in your voice
      build-voice-pack/
        SKILL.md                         # /build-voice-pack -- analyzes your past scripts (run once)
      weekly-batch/
        SKILL.md                         # /weekly-batch -- runs the full pipeline end-to-end
    rules/
      pipeline-rules.md                  # Pipeline conventions
      output-format.md                   # Output schema rules

  pipelines/
    ingest_reddit.py                     # Collects from Reddit via PRAW
    ingest_hn.py                         # Collects from Hacker News (free, no auth)
    ingest_youtube.py                    # Collects from YouTube via yt-dlp (free, no auth)
    ingest_trends.py                     # Collects from Google Trends via trendspyg (free)
    ingest_tiktok.py                     # Optional: TikTok via TikTokApi
    ingest_instagram.py                  # Optional: Instagram via Instaloader
    cluster.py                           # BERTopic clustering + dedup
    retrieve_similar.py                  # Queries ChromaDB for similar past scripts
    index_voice.py                       # Indexes your scripts into ChromaDB

  voice/
    samples/                             # Your 100+ past scripts (one .txt per script)
    STYLE_GUIDE.md                       # Generated by /build-voice-pack
    HOOK_PATTERNS.md                     # Generated by /build-voice-pack
    CTA_PATTERNS.md                      # Generated by /build-voice-pack

  voice_db/                              # ChromaDB local storage (just files on your Mac)

  data/
    raw_trends.json                      # Latest raw data from all sources
    scored_topics.json                   # Scored and ranked topics

  outputs/
    2026-W09/                            # Weekly output folders
      trends.json
      scripts.json
      summary.md
```

---

## Sources

### Claude Code & Agent Skills
- [Claude Code Skills Docs](https://code.claude.com/docs/en/skills)
- [Claude Code Slash Commands](https://code.claude.com/docs/en/slash-commands)
- [Claude Code MCP](https://code.claude.com/docs/en/mcp)
- [Claude Code Memory (CLAUDE.md)](https://code.claude.com/docs/en/memory)
- [Claude Code Subagents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code Hooks](https://code.claude.com/docs/en/hooks)
- [Claude Code Plugins](https://code.claude.com/docs/en/plugins)

### Scraping Tools
- [PRAW GitHub](https://github.com/praw-dev/praw)
- [Instaloader GitHub](https://github.com/instaloader/instaloader)
- [TikTok-Api GitHub](https://github.com/davidteather/TikTok-Api)
- [yt-dlp GitHub](https://github.com/yt-dlp/yt-dlp)
- [trendspyg GitHub](https://github.com/flack0x/trendspyg)
- [facebook-pages-scraper GitHub](https://github.com/SSujitX/facebook-pages-scraper)
- [HN API GitHub](https://github.com/HackerNews/API)
- [Product Hunt API v2](https://api.producthunt.com/v2/docs)

### NLP & Trend Detection
- [BERTopic Docs](https://maartengr.github.io/BERTopic/index.html)
- [BERTrend Paper](https://arxiv.org/html/2411.05930v1)
- [Sentence-Transformers](https://github.com/huggingface/sentence-transformers)

### RAG & Vector Stores
- [Anthropic RAG Cookbook](https://platform.claude.com/cookbook/capabilities-retrieval-augmented-generation-guide)
- [ChromaDB](https://www.trychroma.com/)
- [LanceDB](https://lancedb.com/)

### Automation
- [GitHub Actions Cron Scheduling](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule)
