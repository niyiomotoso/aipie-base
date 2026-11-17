# Visual pass (B-roll)

**Optional and off by default.** Ask before Phase 1; it changes what gets researched
and whether the run produces one video or two. When on, produce both
`<project>-final.mp4` and `<project>-final-visuals.mp4` so he can choose.

## Density and style

- **Five or six moments** in a ~2:40 reel, roughly 10–20% of runtime.
- Keep him on camera for every personal or opinion beat. The story lands on his face.
- **Shot style is mixed, chosen per moment.** Full-frame where the image is strong
  enough to carry the screen; inset where it only supports the point. Record which
  and why.
- Inset geometry that worked: 820×615 at x 130, y 430, with a 6px white border.
- **Stills need motion.** A static image held three seconds reads as a broken video.
  Slow `zoompan` push: `z='min(1+0.0009*on,1.13)'`, centred.

## Finding the moments

**A keyword scan finds mentions, not opportunities.** "I read a paper" is an academic
paper, not teletype paper. Read the sentence.

Look for concrete referents the narration names — a person, a machine, a place, a
document, a year. Skip abstractions; they produce generic stock that cheapens the
video.

## Sources, in priority order

### 1. His own photos — always first

Loose in `Videos Unedited/<project>/`, detected by type. No rights question, and
uniquely his. **Look at every one** before placing it; the filename tells you
nothing. On the ELIZA reel his two photos turned out to be an IBM 1403 printer and
himself at the 1401 exhibit, which answered two different lines.

### 2. Wikimedia Commons — for named historical subjects

No key needed. **A descriptive User-Agent is mandatory** or you get ~10 requests a
minute and then 429s. Never put his email in it; use a project identifier and back
off on `Retry-After`. Space downloads a few seconds apart.

```
action=query&titles=File:...&prop=imageinfo
&iiprop=url|size|extmetadata&format=json&formatversion=2
```

`extmetadata` gives `LicenseShortName`, `LicenseUrl`, `Artist`,
`AttributionRequired` and `Restrictions`.

**Prefer the cleanest licence when several candidates exist.** The top hit for
"Joseph Weizenbaum" is CC BY-SA with a `personality` restriction flag; the second is
plain CC BY at four times the resolution.

ShareAlike is **accepted** — he decided this knowing the copyleft obligation
arguably extends to the reel. Do not re-raise it. Still exclude NonCommercial and
NoDerivatives. Treat a non-empty `Restrictions` field as needing a human look.

### 3. Stock — Pixabay only

**Pexels has paused new API key issuance.** Pixabay works with `PIXABAY_API_KEY`.

Two real limits: the default key caps images at `largeImageURL` ≈1280px, so stock is
**inset-only** until full API access is granted; and generic AI queries return robot
women and neon brains, which would undercut content whose credibility rests on being
thoughtful about AI. **Prefer no visual over bad stock.**

### 4. AI-generated — illustrative only

Fine for abstract concepts and obviously stylised drawings. **Never** photorealistic
depictions of real named people, real historical scenes, or documents. His authority
is built on AI topics; a fabricated "archival" image is a credibility risk, not an
asset choice.

The same caution applies to real images that are not what they appear to be — the
public-domain "ELIZA conversation" on Commons is a **2005 re-creation**, which the
screen itself states. Usable to illustrate the dialogue, misleading if presented as
archival. **Look at every asset.**

## Placement validation — refuse, do not warn

**No B-roll window may straddle a join.** The transition would play underneath the
image and be invisible, which is worse than no transition at all. On the ELIZA reel
this caught two collisions, one missing by 10 milliseconds.

```python
for js, je, transition in join_windows:
    if broll_in < je and broll_out > js:
        refuse(...)
```

Also refuse on a missing asset file or an asset with no licence record.

## Rights ledger

`assets.json`, one record per asset:

```
slug, moment, source, title, source_landing_url, direct_file_url, local_path,
sha256, width, height, license_code, license_url, attribution_required,
creator_name, restrictions, review_required, attribution_string
```

`sha256` plus the moment is what answers "which image is in that reel from two
months ago" if a claim ever arrives.

Write `credits.txt` with a TASL line per asset that requires attribution, and append
those lines to both caption options in `titles-descriptions.txt`. The caption is the
agreed place for credits — no on-screen end card unless he asks, since a card changes
an ending he already approved.
