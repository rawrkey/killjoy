---
description: 'Fuse performance signal and discussion signal into a single niche briefing. Virlo tells you what is performing. `last30days`, when installed, can supply Reddit and X discussion signal; otherwise the agent uses search directives. Use when: user wants a niche briefing, wants signal overlap, wants to know what matters and why, wants validated opportunities, early signals, or format gaps, or needs research prepared for The Forge. Use virlo separately only when the user wants raw performance data without synthesis.'
metadata:
    github-path: skills/content-radar
    github-ref: refs/heads/main
    github-repo: https://github.com/TheMattBerman/openclaw-100k-posts-kit
    github-tree-sha: 67236cc538beee8df4c2f594d48322870e908324
    openclaw:
        emoji: "\U0001F4E1"
        requires:
            env:
                - VIRLO_API_KEY
        user-invocable: true
name: content-radar
---
# Content Radar -- Signal Fusion Briefing System

Content Radar is the **signal fusion and briefing layer** in the pipeline.

Most content research only looks at one signal. You check what's trending on TikTok, or you ask Reddit what people are talking about. But neither alone tells the full story.

**Content Radar fuses two signal types:**

- **Performance Signal (Virlo):** What is actually getting views, shares, and reach right now. Real engagement data from TikTok, Instagram, and YouTube. No guessing.
- **Discussion Signal (Reddit + X):** What your audience is actively asking about, debating, and searching for. If `last30days` is installed, this can be pulled automatically. Otherwise the skill emits search directives for the agent to complete.

The magic is in the overlap. When something is BOTH performing AND being discussed, that is a validated content opportunity. When something is performing but NOT being discussed yet, you found an early signal. When something is being discussed but NOT performing yet, you found an untapped format opportunity.

---

## Pipeline Role

Think of the stack like this:
- **Virlo** = raw performance signal
- **Content Radar** = signal fusion + niche briefing
- **The Forge** = brand-native concept generation
- **Monday Drop** = orchestrated weekly output

Content Radar does NOT replace Virlo. It uses Virlo as one input, adds discussion signal, then tells you what matters and why.

---

## When To Use This Skill

Use Content Radar when you need the **briefing and synthesis layer**.

- Weekly content planning sessions
- Before building out a content calendar
- Before using The Forge skill, output feeds directly in
- Competitive research on a new niche
- Validating a content angle before investing in production
- Deciding what matters and why, not just what is performing
- Finding **overlap**, **early signals**, and **format gaps**

If you only want raw performance data, top videos, outliers, or comet management, use **Virlo** instead.

---

## Setup

### 1. Configure your niche

Create `~/clawd/workspace/content-radar/config.yaml`:

```yaml
niche: "AI Marketing"
virlo_comet_id: "abc-123"
reddit_subreddits:
  - "artificial"
  - "marketing"
  - "aiautomation"
x_search_terms:
  - "ai marketing"
  - "vibe marketing"
```

**Getting your Virlo comet ID:**
```bash
~/clawd/skills/virlo/scripts/virlo.sh list
```

Pick the comet that matches your niche. If you do not have one yet, create it first:
```bash
~/clawd/skills/virlo/scripts/virlo.sh create \
  --name "AI Marketing" \
  --keywords "ai marketing,vibe marketing,ai automation" \
  --platforms "tiktok,instagram,youtube" \
  --cadence "daily" \
  --min-views 1000 \
  --time-range "this_week"
```

### 2. Run a radar scan

```bash
~/clawd/skills/content-radar/scripts/content-radar.sh
```

Or with a specific config:
```bash
~/clawd/skills/content-radar/scripts/content-radar.sh --config ~/clawd/workspace/content-radar/config.yaml
```

Or override just the niche (uses defaults from config):
```bash
~/clawd/skills/content-radar/scripts/content-radar.sh --niche "DTC ecommerce"
```

### Optional: install `last30days`

If you want deeper Reddit/X discussion signal, install [`last30days-skill`](https://github.com/mvanhorn/last30days-skill).

When available as `last30days`, `last30`, or via `LAST30DAYS_CMD`, this skill will use it automatically.
If it is not installed, the skill falls back cleanly to search directives and agent/web research. It should never assume `last30days` exists.

---

## The Two Signal Types

### Signal 1: Performance (Virlo)

Virlo collects short-form and long-form video from TikTok, Instagram, and YouTube based on your keyword configuration. It tells you:

- **Top content by views:** The videos that are actually getting reach. What format, hook, and topic is winning.
- **Breakout creators:** Creators whose recent video massively outperformed their own average. Outlier ratio = viral views divided by their average views. A 10x ratio means this video got 10 times their normal reach. These are your early signals.
- **Trending topics:** The themes that keep showing up in high-performing content.

Performance data is objective. It does not matter if you think a topic is interesting. If it gets 500K views and their average is 20K, the market voted.

### Signal 2: Discussion (Reddit + X)

What people are actively asking, debating, and sharing in community spaces. This reveals:

- **Pain points:** What problems people are trying to solve right now
- **Vocabulary:** The exact words and phrases your audience uses (critical for hooks)
- **Sentiment:** What they love, what they are skeptical about, what they are tired of
- **Trends arriving:** Topics showing up in discussion often become performing content 2-4 weeks later

---

## Reading the Output

The briefing is structured in four sections:

### What's PERFORMING (Virlo)
The raw video intelligence. Look at these for format inspiration. What length? What hook style? What production quality? The title and view count combination tells you a lot.

### What's Being DISCUSSED (Reddit + X)
The community pulse. Look for frustration, curiosity, and questions. These are the emotions that convert to views when turned into content.

### Pattern Analysis
**This is the most important section.** The agent completes the pattern matching after the discussion signal is available, either from `last30days` or from the emitted search directives:

- **Overlap** = high-confidence opportunities. Both signals agree this matters.
- **Performing but not discussed** = early signal. You could be first to the discussion.
- **Discussed but not performing** = format gap. The audience wants this but no one has figured out how to make it perform yet.

### Content DNA Breakdowns
For each outlier video, a 7-dimension analysis (Topic, Angle, Hook Structure, Story Structure, Visual Format, Key Visuals, Audio). Videos that are visual-first (demo, reaction, minimal description) are flagged for manual 30-second review with the direct URL and specific diagnostic questions.

### Raw Data for The Forge
A clean structured list ready to copy into The Forge skill for content generation. Now includes direct video URLs for every item.

---

## Workflow Example

1. Run Content Radar on Monday morning
2. Review the Pattern Analysis section
3. Pick 2-3 topics from the Overlap and Early Signal categories
4. Feed Raw Data for The Forge into The Forge skill
5. Generate content for the week

---

## Config Reference

| Field | Required | Description |
|-------|----------|-------------|
| `niche` | Yes | Human-readable name for the briefing header |
| `virlo_comet_id` | Yes | The Virlo comet ID to pull data from |
| `reddit_subreddits` | Yes | List of subreddits to scan (no r/ prefix needed) |
| `x_search_terms` | Yes | List of search terms to find X conversations |

---

## Notes

- Virlo data requires an active comet with at least one completed run. New comets have no data until the first scheduled collection finishes.
- Reddit and X searches use live web search. Results reflect what is currently indexed.
- Run this skill weekly for ongoing content planning. Monthly for new niche exploration.
- The config file is reusable. Once set up, just run the script.
