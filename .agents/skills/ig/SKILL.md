---
allowed-tools:
    - Read
    - Write
    - Edit
    - Bash
    - Grep
    - Glob
    - WebFetch
    - WebSearch
    - Agent
argument-hint: '[reel|hook|caption|story|carousel|analyze|audit|competitor|calendar|strategy|affiliate|comment|repurpose] [topic-or-file]'
compatibility: Requires Claude Code. Python 3.12+ optional for analysis scripts.
description: |
    Full-lifecycle Instagram content engine with 13 sub-skills, 6 specialized agents, and 5-category 100-point scoring. Optimized for the 2026 Instagram algorithm (watch time, DM-sends, saves). Creates Reels, Stories, Carousels, hooks, captions, affiliate posts, and editorial calendars. Analyzes post performance via Instagram Graph API, audits content quality, researches competitors, and repurposes content cross-platform. Niche detection for fitness, beauty, food, business, education, lifestyle, and creator accounts. Use when user says "Reel", "Hook", "Caption", "Story", "Carousel", "Instagram", "IG", "Post planen", "Content-Plan", "Affiliate Post", "Performance", "Competitor", "Reels analysieren", "posting schedule", "ig audit", "content score", "hook schreiben", "reel skript", "instagram strategy", "content calendar", "engagement analysis".
license: MIT
metadata:
    author: NicoJunk
    github-path: skills/ig
    github-ref: refs/heads/main
    github-repo: https://github.com/nicojunk/claude-ig
    github-tree-sha: da567ccc74080e94da35b6595cfca3e6d45c0db6
    version: 2.0.0
name: ig
user-invocable: true
---
# IG: Instagram Content Engine

Full-lifecycle Instagram management: hooks, Reels, Stories, Carousels, captions,
affiliate content, performance analysis, competitor research, editorial planning,
and content repurposing. Optimized for the 2026 Instagram algorithm with
watch time, DM-sends, and saves as primary distribution signals.

Works for any Instagram account and niche. Detects account context from API data
and adapts content strategy, hook patterns, and scoring calibration accordingly.

## Quick Reference

| Command | What it does |
|---------|-------------|
| `/ig reel <topic>` | Write a complete Reel (hook, script, caption, thumbnail) |
| `/ig hook <topic>` | Generate and score hooks for any format |
| `/ig caption <topic>` | Write an optimized caption (500+ chars, save CTA) |
| `/ig story <topic>` | Plan a Story sequence (slides, stickers, polls) |
| `/ig carousel <topic>` | Plan a Carousel (cover hook, slides, CTA) |
| `/ig analyze [post-url]` | Analyze post performance via Instagram API |
| `/ig audit` | Full content audit with parallel subagent delegation |
| `/ig competitor <accounts>` | Research competitor content |
| `/ig calendar [weekly\|monthly]` | Generate an editorial content calendar |
| `/ig strategy` | Content strategy and positioning analysis |
| `/ig affiliate <partner>` | Create compliant affiliate content |
| `/ig comment` | Comment response strategy and automation |
| `/ig repurpose <post>` | Repurpose IG content for other platforms |

## Orchestration Logic

### Command Routing

1. Parse the user's command to determine the sub-skill
2. If no sub-command given, ask which action they need
3. Route to the appropriate sub-skill:
   - `reel` / `skript` / `video` -> `ig-reel` (full Reel production)
   - `hook` / `opening` -> `ig-hook` (hook generation and scoring)
   - `caption` / `beschreibung` / `text` -> `ig-caption` (caption writing)
   - `story` / `stories` -> `ig-story` (Story sequence planning)
   - `carousel` / `karussell` / `slides` -> `ig-carousel` (Carousel planning)
   - `analyze` / `analyse` / `performance` / `insights` -> `ig-analyze` (API-driven analysis)
   - `audit` / `check` / `health` -> `ig-audit` (full content audit with subagents)
   - `competitor` / `konkurrenz` / `research` / `spy` -> `ig-competitor` (competitor research)
   - `calendar` / `plan` / `kalender` / `schedule` -> `ig-calendar` (editorial calendar)
   - `strategy` / `strategie` / `positioning` -> `ig-strategy` (positioning and content mix)
   - `affiliate` / `werbung` / `kooperation` / `sponsored` -> `ig-affiliate` (compliant partner content)
   - `comment` / `kommentar` / `replies` -> `ig-comment` (comment response)
   - `repurpose` / `redistribute` / `cross-post` -> `ig-repurpose` (cross-platform repurposing)

### Niche Detection

Detect account niche from bio, content patterns, and hashtag analysis:

| Signal | Niche | Adaptation |
|--------|-------|-----------|
| Workout demos, exercise names, body part focus | Fitness | Correction hooks, body-part targeting, safe exercise form |
| Recipe posts, nutrition tips, meal prep | Food / Nutrition | Recipe format templates, ingredient lists, macro data |
| Product reviews, tutorials, before/after | Beauty / Skincare | Transformation hooks, product comparison carousels |
| Tips, frameworks, income proof | Business / Coaching | Authority hooks, case study carousels, lead magnet CTAs |
| Lessons, how-to, step-by-step | Education | Curiosity gap hooks, carousel-heavy strategy |
| Day-in-life, travel, personal stories | Lifestyle | Identity trigger hooks, story-heavy strategy |
| Mixed / unclear | Creator | Analyze top 10 posts to determine primary content type |

Adapt hook library selection, caption voice, CTA strategy, and content mix
recommendations based on detected niche. If the user has configured
`references/account-baseline.md`, use that data instead of detecting.

### Algorithm Priority (2026)

Every piece of content is optimized in this priority order:

| Priority | Signal | Weight | Why |
|----------|--------|--------|-----|
| 1 | Watch Time | Highest | First 3 seconds determine distribution. Completion rate is king. |
| 2 | DM-Sends per Reach | 3-5x likes | Primary signal for reaching new audiences via Explore |
| 3 | Saves | ~3x likes | Signal for lasting value, drives Explore and Suggested placement |
| 4 | Likes/Comments | Lowest | Weakest signals; comments without saves = algorithm ignores |
| 5 | Originality Score | Gate | Recycled formats tank reach; always adapt through creator's unique lens |

## Quality Gates

Hard rules. Content that violates any gate is blocked from delivery:

| # | Gate | Threshold |
|---|------|-----------|
| G1 | Score before delivery | NEVER deliver content without a Content Quality Score |
| G2 | Em dashes | NEVER use em dashes (U+2014) in any output |
| G3 | Affiliate disclosure | NEVER create affiliate content without proper disclosure at caption TOP |
| G4 | Controversial opinions | NEVER recommend controversial opinion posts (high comments, zero saves) |
| G5 | Affiliate spacing | NEVER place 2 affiliate posts on consecutive days |
| G6 | Metrics guessing | NEVER guess account metrics; use API data or state data is unavailable |
| G7 | Safe zones | NEVER place text in format-specific unsafe zones (check format-specs.md) |

## Scoring Methodology

### Content Quality Score (0-100)

5-category weighted scoring from `references/scoring-system.md`:

| Category | Weight | What it measures |
|----------|--------|-----------------|
| Hook Strength | 25 pts | Curiosity gap, pattern interrupt, identity trigger, first 3s clarity |
| Content Quality | 25 pts | Value density, structure, problem-solution flow, voice authenticity |
| Caption & CTA | 20 pts | Length (500+ chars), save/DM CTA, hook variation opener, hashtag quality |
| Format Compliance | 15 pts | Correct specs, safe zones, thumbnail, duration targets |
| Algorithm Signals | 15 pts | Save/DM optimization, originality, non-controversial, watch time design |

### Scoring Bands

| Score | Grade | Rating | Action |
|-------|-------|--------|--------|
| 90-100 | A | Publish | Ready to post, flagship content |
| 80-89 | B | Strong | Minor polish, ready for publication |
| 60-79 | C | OK | Targeted improvements needed (must include fix instructions) |
| 40-59 | D | Below Standard | Significant rework required |
| < 40 | F | Reject | Fundamental issues, start over |

Content scoring below 80 MUST include specific revision instructions per
deficient category. Do not just deliver the score.

### Priority Levels (for audit findings)

- **Critical**: Content violates a Quality Gate (fix immediately)
- **High**: Score < 60, significant performance drag (fix before posting)
- **Medium**: Score 60-79, optimization opportunity (improve within week)
- **Low**: Minor polish, best practice (backlog)

## Reference Files

Load on-demand as needed. NEVER load all references at startup.

**Path resolution:** All references at `~/.claude/skills/ig/references/`.
Sub-skills referencing `references/*.md` resolve to this path.

| Reference | Content | Used by |
|-----------|---------|---------|
| `references/algorithm-2026.md` | Algorithm signals, ranking factors, distribution mechanics | All sub-skills |
| `references/format-specs.md` | Technical specs per format (Reel, Story, Carousel, Feed) with safe zones | ig-reel, ig-story, ig-carousel |
| `references/scoring-system.md` | Full 5-category scoring rubric with sub-criteria and severity multipliers | All content sub-skills, ig-audit |
| `references/hook-library.md` | 50+ hook templates in 5 categories with scoring and adaptation rules | ig-hook, ig-reel, ig-carousel |
| `references/content-rules.md` | Caption structure, CTA hierarchy, hashtag strategy, voice guidelines | ig-caption, ig-reel, ig-story |
| `references/account-baseline.md` | Account metrics template, API integration, KPI tracking methodology | ig-analyze, ig-strategy, ig-calendar |
| `references/affiliate-compliance.md` | Disclosure requirements, partner management, scheduling rules | ig-affiliate |
| `references/conversion-pipeline.md` | DM automation, link tracking, funnel architecture | ig-caption, ig-strategy |
| `references/competitor-framework.md` | Competitor monitoring methodology, benchmarks, trend detection | ig-competitor |
| `references/story-strategy.md` | Story types, slide sequences, interactive elements, retention rules | ig-story |
| `references/comment-responder.md` | Comment strategy, response categories, automation patterns | ig-comment |
| `references/repurpose-playbook.md` | Cross-platform adaptation rules per channel | ig-repurpose |

## Sub-Skills

This skill orchestrates 13 specialized sub-skills:

| # | Sub-Skill | Purpose |
|---|-----------|---------|
| 1 | `ig-reel` | Full Reel production (hook, script, caption, thumbnail) |
| 2 | `ig-hook` | Hook generation, scoring, and A/B variants |
| 3 | `ig-caption` | Caption writing with save CTA, hashtags, 500+ chars |
| 4 | `ig-story` | Story sequence planning (slides, stickers, polls) |
| 5 | `ig-carousel` | Carousel planning (cover, slides, CTA structure) |
| 6 | `ig-analyze` | Post/account performance analysis via Instagram API |
| 7 | `ig-audit` | Full content audit with parallel subagent delegation |
| 8 | `ig-competitor` | Competitor research and benchmarking |
| 9 | `ig-calendar` | Editorial calendar with content mix validation |
| 10 | `ig-strategy` | Content positioning, niche analysis, growth strategy |
| 11 | `ig-affiliate` | Compliant affiliate/sponsored content |
| 12 | `ig-comment` | Comment response strategy and automation |
| 13 | `ig-repurpose` | Cross-platform content repurposing |

## Agents

For parallel analysis during `/ig audit`:

| Agent | Role | Tools |
|-------|------|-------|
| `ig-content` | Content quality assessment across recent posts | Read, Grep, Glob |
| `ig-engagement` | Engagement pattern analysis (saves, shares, DMs) | Read, Bash |
| `ig-creative` | Visual and format compliance check | Read, Grep |
| `ig-growth` | Follower growth, reach trends, posting frequency | Read, Bash |
| `ig-competitor` | Competitor benchmarking and gap analysis | Read, WebSearch, WebFetch |
| `ig-compliance` | Affiliate disclosure, safe zones, Quality Gate checks | Read, Grep, Glob |

### Agent Details

**ig-content**: Spawned as subagent during `/ig audit`. Reads recent posts,
scores each against the 5-category rubric, identifies patterns in top/bottom
performers. Outputs: per-post scores, category averages, content mix analysis.

**ig-engagement**: Analyzes engagement metrics from API data. Calculates save
rates, DM-send rates, completion rates. Identifies which hook categories and
content types drive the highest engagement. Outputs: engagement heatmap,
best/worst performers by signal type.

**ig-creative**: Checks format compliance across recent posts. Validates safe
zones, duration targets, thumbnail quality. Flags posts violating format-specs.md.
Outputs: compliance checklist, violation list, format distribution.

**ig-growth**: Tracks follower growth rate, reach trends, posting frequency
impact. Correlates posting schedule with performance. Outputs: growth metrics,
optimal posting frequency and timing.

**ig-competitor**: Compares account metrics against niche benchmarks. Identifies
content gaps (topics competitors cover that account doesn't). Spots trending
formats and hook patterns. Outputs: competitive positioning, actionable gaps.

**ig-compliance**: Checks affiliate posts for proper disclosure, validates
Quality Gate adherence across all recent content. Outputs: compliance report,
violation flags with post references.

## Execution Flow

Standard execution order for `/ig reel`:

1. **Parse**: Identify topic, detect content type and niche context
2. **Load References**: format-specs.md + hook-library.md + content-rules.md
3. **Hook**: Generate 3 hook variants from different categories, score each, select best
4. **Script**: Structure body (problem -> solution -> insight) with segment timing
5. **Caption**: Write 500+ char caption with save CTA and niche hashtags
6. **Thumbnail**: Describe thumbnail concept with text overlay
7. **Score**: Apply full 5-category Content Quality Score
8. **Deliver**: Output complete package with score and revision notes

For `/ig analyze`, steps 1-2 run, then API calls replace steps 3-7 with data analysis.
For `/ig audit`, all 6 agents spawn in parallel, results aggregate into unified report.

## Instagram API Integration

### Graph API Authentication

Instagram data is accessed via the **Facebook Graph API** at `https://graph.facebook.com/v21.0`.
Do NOT use `graph.instagram.com` (that endpoint rejects Page Tokens).

**Two-Token System:**
- **User Token** (`INSTAGRAM_ACCESS_TOKEN`): For ads, user-level queries
- **Page Token** (`META_PAGE_TOKEN`): Required for all Instagram content endpoints (media, insights, stories)

If `META_PAGE_TOKEN` is stale or missing, derive a fresh one:
```bash
source ~/Desktop/.env
PT=$(curl -s "https://graph.facebook.com/v21.0/$META_PAGE_ID?fields=access_token&access_token=$INSTAGRAM_ACCESS_TOKEN" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

**Environment variables** (load with `source ~/Desktop/.env`):
- `INSTAGRAM_ACCESS_TOKEN`: Long-Lived User Token
- `META_PAGE_TOKEN`: Page Token (required for content endpoints)
- `INSTAGRAM_BUSINESS_ACCOUNT_ID`: IG Business Account ID
- `META_PAGE_ID`: Facebook Page ID (for token derivation)
- `META_AD_ACCOUNT_ID`: Ad Account ID (for ads endpoints)

### Endpoints

```
Base URL: https://graph.facebook.com/v21.0
Auth: Page Token for content, User Token for ads
Rate Limit: 200 calls/hour per token

Content endpoints (Page Token):
  GET /{ig-id}?fields=id,username,media_count,followers_count,follows_count,biography,website,profile_picture_url
  GET /{ig-id}/media?fields=id,caption,media_type,thumbnail_url,timestamp,like_count,comments_count,permalink&limit=50
  GET /{media-id}/insights?metric=reach,saved,shares,likes,comments,total_interactions
  GET /{ig-id}/insights?metric=reach,follower_count,profile_views&period=day&since={unix}&until={unix}
  GET /{ig-id}/insights?metric=accounts_engaged,total_interactions&metric_type=total_value&period=day&since={unix}&until={unix}
  GET /{ig-id}/stories?fields=id,media_type,timestamp
```

**IMPORTANT:** Do NOT request `impressions` or `plays` (deprecated for Reels in v22+).
`accounts_engaged` requires `metric_type=total_value` and cannot be mixed with time-series metrics.

### Script Usage

The `scripts/analyze_post.py` script handles token management automatically:
```bash
source ~/Desktop/.env
python3 scripts/analyze_post.py --user-id $INSTAGRAM_BUSINESS_ACCOUNT_ID --token $INSTAGRAM_ACCESS_TOKEN --page-token $META_PAGE_TOKEN --page-id $META_PAGE_ID
```
If `--page-token` is omitted, the script derives one from `--token` + `--page-id`.

### Graceful Degradation

If API access is not configured or token is expired:
1. Inform the user that live data is unavailable
2. Fall back to data in `references/account-baseline.md` (if populated)
3. Clearly mark any analysis as "based on cached data, not live"
4. Never fabricate metrics

## Setup: Account Configuration

After installation, configure for your account:

1. **Populate account-baseline.md** with your account metrics:
   - Run `/ig analyze` to pull live data via API
   - Or manually enter: followers, avg engagement, top posts, posting schedule
2. **Set API credentials** in your `.env` file
3. **Customize hook-library.md** with hooks that work in your niche
4. **Run `/ig audit`** to establish your baseline scores

The skill works without configuration (using general best practices), but
performs significantly better with account-specific data.

## Anti-Patterns (Never Do These)

| Anti-Pattern | Why |
|-------------|-----|
| Deliver without score | Incomplete deliverable; score is mandatory |
| Use em dashes | #1 signal of AI-generated text |
| Generic hashtags (#fitness, #motivation) | Zero distribution value, signals low effort |
| Controversial opinion posts | High comments, zero saves = algorithm ignores |
| Copy competitor hooks verbatim | Originality Score (2026) penalizes recycled formats |
| Guess metrics | Stale data leads to wrong decisions; use API or state uncertainty |
| Skip format-specs.md | Wrong specs = reduced reach (safe zones, duration, ratio) |
| Affiliate without disclosure | Legal violation in most jurisdictions |
| Optimize for likes over saves | Likes are the weakest algorithm signal |
| Wall-of-text captions | Line breaks mandatory for readability and retention |
| Post at the same time every day | Algorithm rewards variation within optimal windows |
