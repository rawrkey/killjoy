#!/usr/bin/env bash
# content-radar.sh
# Niche Briefing: fuse Virlo performance data with Reddit/X discussion signals.
# Outputs a structured markdown briefing ready to feed into The Forge skill.
#
# Usage:
#   ./content-radar.sh
#   ./content-radar.sh --config /path/to/config.yaml
#   ./content-radar.sh --niche "DTC ecommerce"
#   ./content-radar.sh --comet-id abc-123

set -euo pipefail

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
OPENCLAW_HOME="${OPENCLAW_HOME:-$HOME/clawd}"
WORKSPACE="$OPENCLAW_HOME/workspace/content-radar"
DEFAULT_CONFIG="$WORKSPACE/config.yaml"
VIRLO_SCRIPT="$OPENCLAW_HOME/skills/virlo/scripts/virlo.sh"
OUTPUT_DIR="$WORKSPACE/briefings"
LAST30DAYS_CMD="${LAST30DAYS_CMD:-}"
LAST30DAYS_SCRIPT_OVERRIDE="${LAST30DAYS_SCRIPT:-}"

# ── Defaults ──────────────────────────────────────────────────────────────────
CONFIG_FILE="$DEFAULT_CONFIG"
OVERRIDE_NICHE=""
OVERRIDE_COMET=""
TOP_VIDEOS=10
TOP_OUTLIERS=5
VIRLO_LOOKBACK_DAYS="${VIRLO_LOOKBACK_DAYS:-30}"

# ── Argument Parsing ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --config)    CONFIG_FILE="$2";   shift 2 ;;
    --niche)     OVERRIDE_NICHE="$2"; shift 2 ;;
    --comet-id)  OVERRIDE_COMET="$2"; shift 2 ;;
    --limit)     TOP_VIDEOS="$2";    shift 2 ;;
    --help|-h)
      echo "Usage: content-radar.sh [--config FILE] [--niche NAME] [--comet-id ID] [--limit N]"
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# ── Helpers ───────────────────────────────────────────────────────────────────
require_cmd() {
  command -v "$1" &>/dev/null || { echo "ERROR: '$1' not found. Install it and retry." >&2; exit 1; }
}

date_days_ago_utc() {
  python3 - "$1" <<'PY'
from datetime import datetime, timedelta, timezone
import sys

days = int(sys.argv[1])
print((datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d"))
PY
}

read_yaml_field() {
  # Minimal YAML field reader - handles simple key: value and key: "value"
  local file="$1" field="$2"
  grep -E "^${field}:" "$file" 2>/dev/null \
    | sed "s/^${field}:[[:space:]]*//" \
    | tr -d '"' \
    | head -1
}

read_yaml_list() {
  # Read a simple YAML list block and return comma-separated values
  # NOTE: save original $0 before gsub so the reset check sees the unmodified line
  local file="$1" field="$2"
  awk "/^${field}:/{found=1; next}
       found {
         orig = \$0
         if (orig ~ /^  - /) {
           gsub(/^  - /, \"\")
           gsub(/\"/, \"\")
           printf \"%s,\", \$0
         } else {
           found = 0
         }
       }" "$file" \
    | sed 's/,$//'
}

detect_last30days_script() {
  if [[ -n "$LAST30DAYS_CMD" && -x "$LAST30DAYS_CMD" ]]; then
    echo "$LAST30DAYS_CMD"
    return 0
  fi
  if [[ -n "$LAST30DAYS_SCRIPT_OVERRIDE" && -r "$LAST30DAYS_SCRIPT_OVERRIDE" ]]; then
    echo "$LAST30DAYS_SCRIPT_OVERRIDE"
    return 0
  fi
  local candidates=(
    "$OPENCLAW_HOME/external/last30days-skill/scripts/last30days.py"
    "$OPENCLAW_HOME/skills/last30days/scripts/last30days.py"
    "$OPENCLAW_HOME/openclaw-skills-repo/skills/zats/last30days/scripts/last30days.py"
    "$OPENCLAW_HOME/skills/last30days-old/scripts/last30days.py"
  )
  local candidate
  for candidate in "${candidates[@]}"; do
    if [[ -f "$candidate" && -r "$candidate" ]]; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

normalize_last30days_summary() {
  local raw="$1"
  LAST30_RAW="$raw" python3 <<'PY'
import os
import re

raw = os.environ.get("LAST30_RAW", "")
reddit = []
x_posts = []
notes = []
research_stats = []
source_highlights = []
key_patterns = []
ranked_findings = []
current_section = None

for line in raw.splitlines():
    stripped = line.strip()
    if not stripped:
        current_section = None
        continue
    if stripped.startswith("#"):
        continue

    bullet = stripped
    if bullet.startswith("- "):
        bullet = bullet[2:].strip()

    normalized = re.sub(r"^\d+\.\s*", "", bullet)
    lower = normalized.lower()

    if lower.rstrip(":") == "key patterns discovered":
        current_section = "key_patterns"
        continue
    if lower.rstrip(":") in {"top mentions", "most mentioned", "ranked findings"}:
        current_section = "ranked_findings"
        continue

    if lower.startswith("reddit:"):
        current_section = None
        reddit.append(normalized.split(":", 1)[1].strip())
    elif lower.startswith("x:") or lower.startswith("twitter:"):
        current_section = None
        x_posts.append(normalized.split(":", 1)[1].strip())
    elif lower.startswith("research stats:"):
        current_section = None
        research_stats.append(normalized.split(":", 1)[1].strip())
    elif lower.startswith("sources:"):
        current_section = None
        source_highlights.extend(
            [part.strip() for part in normalized.split(":", 1)[1].split(",") if part.strip()]
        )
    elif current_section == "key_patterns":
        key_patterns.append(normalized)
    elif current_section == "ranked_findings":
        ranked_findings.append(normalized)
    else:
        notes.append(normalized)

print("### Reddit Themes")
print()
if reddit:
    for item in reddit:
        print(f"- {item}")
else:
    print("- No Reddit-specific themes extracted from last30days output.")

print()
print("### X Conversations")
print()
if x_posts:
    for item in x_posts:
        print(f"- {item}")
else:
    print("- No X-specific conversations extracted from last30days output.")

if notes:
    print()
    print("### Cross-Platform Notes")
    print()
    for item in notes:
        print(f"- {item}")

if key_patterns:
    print()
    print("### Key Patterns")
    print()
    for item in key_patterns:
        print(f"- {item}")

if ranked_findings:
    print()
    print("### Ranked Findings")
    print()
    for item in ranked_findings:
        print(f"- {item}")

if research_stats:
    print()
    print("### Research Stats")
    print()
    for item in research_stats:
        print(f"- {item}")

if source_highlights:
    print()
    print("### Source Highlights")
    print()
    for item in source_highlights:
        print(f"- {item}")
PY
}

render_last30days_sections() {
  local json_file="$1" niche="$2"
  # Pass config context to Python for dynamic keyword building
  RADAR_SUBREDDITS="$SUBREDDITS" \
  RADAR_XTERMS="$X_TERMS" \
  BRAND_VOICE_FILE="${BRAND_VOICE_FILE:-$OPENCLAW_HOME/workspace/brand/voice-profile.md}" \
  python3 - "$json_file" "$niche" <<'PY'
import json, re, sys
from collections import Counter

json_file, niche = sys.argv[1], sys.argv[2]
with open(json_file) as f:
    data = json.load(f)

# ── Niche relevance filtering ──────────────────────────────────────────────
# The raw last30days output contains ALL results including irrelevant subreddits
# (r/meirl, r/wallstreetbets, r/meme). Filter by niche keywords before selecting.

niche_lower = niche.lower()
niche_words = set(re.findall(r'[a-z]{3,}', niche_lower))

# ── Build relevance keywords dynamically ──────────────────────────────────
# Sources: niche name, config subreddits/X terms, brand voice vocabulary
#
# Universal core (applies to all niches):
RELEVANCE_KEYWORDS = niche_words | {
    'startup', 'growth', 'scale', 'scaling', 'brand', 'content', 'creator',
    'tool', 'tools', 'workflow', 'automation', 'automate', 'strategy',
    'revenue', 'funding', 'launch', 'product', 'feature', 'update',
    'trend', 'trending', 'viral', 'engagement', 'audience', 'conversion',
    'campaign', 'agency', 'freelance', 'founder', 'ceo', 'entrepreneur',
    'platform', 'software', 'benchmark', 'performance', 'productivity',
}

# Add niche-specific keywords from config (subreddits + search terms)
import os
config_subs = os.environ.get('RADAR_SUBREDDITS', '')
config_xterms = os.environ.get('RADAR_XTERMS', '')
for term in config_subs.split(',') + config_xterms.split(','):
    for word in re.findall(r'[a-z]{3,}', term.lower()):
        if word not in {'com', 'www', 'http', 'https', 'the', 'and', 'for'}:
            RELEVANCE_KEYWORDS.add(word)

# Extract ONLY specific named entities and jargon from brand voice file.
# DO NOT extract from descriptive prose — words like "data", "growth", "market"
# are too generic and cause false matches across unrelated industries.
voice_file = os.environ.get('BRAND_VOICE_FILE', '')
if voice_file and os.path.isfile(voice_file):
    with open(voice_file) as vf:
        voice_text = vf.read()

    # 1. Pull proper nouns from example phrases (company/product names)
    #    Only CamelCase or ALL-CAPS words that are likely brand names
    example_match = re.search(r'(?:Example|On-brand).*?\n(.*?)(?:Off-brand|\Z)', voice_text, re.S | re.I)
    if example_match:
        # Named entities: capitalized words that aren't sentence starters
        for word in re.findall(r'(?<!\. )[A-Z][a-z]{2,}(?:AI|GPT)?', example_match.group(1)):
            if word not in {'Here', 'That', 'The', 'This', 'Nobody', 'Jack', 'Junior', 'Stock'}:
                RELEVANCE_KEYWORDS.add(word.lower())

    # 2. Pull from Jargon level description (domain-specific terms only)
    jargon_match = re.search(r'[Jj]argon.*?[:—]\s*(.*?)(?:\n\n|\n\*\*|\Z)', voice_text)
    if jargon_match:
        # Terms in quotes are explicit jargon
        for term in re.findall(r'"([^"]+)"', jargon_match.group(1)):
            for word in term.lower().split():
                if len(word) > 2:
                    RELEVANCE_KEYWORDS.add(word)

# Subreddits that are never relevant for AI/marketing niche
JUNK_SUBS = {
    # Meme/humor
    'meirl', 'me_irl', 'meme', 'memes', 'dankmemes', 'funny', 'pics',
    'wholesomememes', 'sipstea', 'facepalm', 'therewasanattempt',
    'murderedbywords', 'cursedcomments', 'holup', 'shitposting',
    # General Q&A
    'askreddit', 'showerthoughts', 'tifu', 'amitheasshole', 'nostupidquestions',
    'outoftheloop', 'explainlikeimfive', 'todayilearned',
    # Lifestyle/location (not relevant to most niches)
    'gaming', 'movies', 'television', 'music', 'food', 'cooking',
    'relationships', 'dating_advice', 'fitness', 'loseit',
    'personalfinance', 'realestate', 'auspropertychat', 'bayarearealestate',
    'legaladvice', 'cars', 'diy', 'homeimprovement',
    # Politics/news (too broad)
    'politics', 'worldnews', 'news', 'conservative', 'liberal',
}

def relevance_score(text):
    """Score text by how many niche keywords appear."""
    words = set(re.findall(r'[a-z]{3,}', (text or '').lower()))
    return len(words & RELEVANCE_KEYWORDS)

def get_subreddit_name(post):
    """Extract subreddit name — handles string, dict, and stringified-dict formats."""
    import ast
    sub = post.get('subreddit', '')
    if isinstance(sub, dict):
        return (sub.get('name') or sub.get('display_name') or sub.get('id', '')).lower()
    name = str(sub).strip()
    # last30days sometimes serializes the subreddit dict as a Python repr string
    if name.startswith('{') and "'name'" in name:
        try:
            d = ast.literal_eval(name)
            if isinstance(d, dict):
                return (d.get('name') or d.get('id', '')).lower()
        except:
            pass
    name = name.lower()
    if not name:
        url = post.get('url', '')
        m = re.search(r'/r/(\w+)', url)
        if m:
            return m.group(1).lower()
    return name

def is_relevant_reddit(post):
    sub = get_subreddit_name(post)
    if sub in JUNK_SUBS:
        return False
    title = post.get('title', '')
    insights = ' '.join(post.get('comment_insights', [])[:3])
    combined = f"{title} {insights} {post.get('why_relevant', '')}"
    # Need at least 2 niche keyword matches to pass filter
    return relevance_score(combined) >= 2

def is_relevant_x(post):
    text = post.get('text', '') or ''
    why = post.get('why_relevant', '') or ''
    return relevance_score(f"{text} {why}") >= 2

# Filter and sort by relevance
all_reddit = data.get('reddit', [])
all_x = data.get('x', [])
all_hn = data.get('hackernews', [])
all_yt = data.get('youtube', [])

reddit = sorted(
    [r for r in all_reddit if is_relevant_reddit(r)],
    key=lambda r: relevance_score(r.get('title','') + ' ' + ' '.join(r.get('comment_insights',[])[:3])),
    reverse=True
)[:8]

xposts = sorted(
    [x for x in all_x if is_relevant_x(x)],
    key=lambda x: relevance_score(x.get('text','') + ' ' + x.get('why_relevant','')),
    reverse=True
)[:5]

# HN and YouTube don't need heavy filtering (already niche-searched)
hn = all_hn[:5]
yt = all_yt[:3]

# ── Helper functions ───────────────────────────────────────────────────────

stop = {
    'the','and','for','that','with','this','from','what','your','about','into',
    'they','have','just','more','than','when','will','their','there','been',
    'them','over','most','using','used','need','how','why','are','you','our',
    'out','not','all','can','its','was','his','her','she','him','but','has',
    'had','who','too','any','does','did','because','after','before','where',
    'which','while','want','gets','get','make','made','reddit','twitter','post','thread',
}

def clean(text):
    return re.sub(r'\s+', ' ', (text or '').replace('|', '/').replace('<strong>','').replace('</strong>','')).strip()

def short(text, n=140):
    t = clean(text)
    return t if len(t) <= n else t[:n-1] + '…'

def extract_keywords(texts, limit=8):
    c = Counter()
    for text in texts:
        for token in re.findall(r"[A-Za-z][A-Za-z\-']{3,}", (text or '').lower()):
            if token in stop:
                continue
            c[token] += 1
    return [w for w,_ in c.most_common(limit)]

reddit_texts = [r.get('title','') + ' ' + ' '.join(r.get('comment_insights',[])[:2]) + ' ' + r.get('why_relevant','') for r in reddit]
x_texts = [x.get('text','') + ' ' + x.get('why_relevant','') for x in xposts]
hn_texts = [h.get('title','') for h in hn]
all_keywords = extract_keywords(reddit_texts + x_texts + hn_texts, limit=10)
validated = all_keywords[:4]
early = all_keywords[4:7]

# ── Output ─────────────────────────────────────────────────────────────────

print("## What's Being DISCUSSED (Reddit + X)")
print("")
print(f"Filtered {len(reddit)} relevant Reddit posts from {len(all_reddit)} total, "
      f"{len(xposts)} relevant X posts from {len(all_x)} total.")
print("")

print("### Reddit Discussions")
print("")
for i, row in enumerate(reddit, 1):
    sub = get_subreddit_name(row) or 'unknown'
    title = clean(row.get('title', 'Untitled'))
    url = row.get('url', '')
    insights = row.get('comment_insights', [])
    top_insight = clean(insights[0]) if insights else ''
    print(f"**{i}. [{title[:80]}]({url})**")
    print(f"   r/{sub} | score: {row.get('score', '?')}")
    if top_insight:
        print(f"   > {short(top_insight, 200)}")
    print("")

if not reddit:
    print("No relevant Reddit threads found for this niche.\n")

print("### X/Twitter Signal")
print("")
for i, row in enumerate(xposts, 1):
    text = clean(row.get('text', ''))
    handle = row.get('author_handle', '')
    url = row.get('url', '')
    if handle:
        print(f"**{i}. @{handle}:** {short(text, 200)}")
    else:
        print(f"**{i}.** {short(text, 200)}")
    if url:
        print(f"   {url}")
    print("")

if not xposts:
    print("No relevant X posts found for this niche.\n")

if hn:
    print("### Hacker News")
    print("")
    for i, row in enumerate(hn, 1):
        title = clean(row.get('title', ''))
        url = row.get('url', '')
        print(f"**{i}. {title}**")
        if url:
            print(f"   {url}")
        print("")

if yt:
    print("### YouTube")
    print("")
    for i, row in enumerate(yt, 1):
        title = clean(row.get('title', ''))
        url = row.get('url', '')
        channel = row.get('channel', '') or row.get('author', '')
        print(f"**{i}. {title}**")
        if channel:
            print(f"   by {channel}")
        if url:
            print(f"   {url}")
        print("")

print("---\n")

print("## Pattern Analysis\n")
print("### Validated Topics (appear across multiple sources)")
if validated:
    for kw in validated:
        # Find which sources mention this keyword
        sources = []
        for r in reddit:
            if kw.lower() in (r.get('title','') + ' '.join(r.get('comment_insights',[])[:2])).lower():
                sources.append(f"r/{get_subreddit_name(r)}")
                break
        for x in xposts:
            if kw.lower() in (x.get('text','') + x.get('why_relevant','')).lower():
                sources.append("X")
                break
        for h in hn:
            if kw.lower() in h.get('title','').lower():
                sources.append("HN")
                break
        source_str = ', '.join(sources) if sources else 'multiple sources'
        print(f"- **{kw.title()}** — appearing in {source_str}")
else:
    print("- Discussion signal was sparse. No strong cross-source overlap found.")

print("\n### Emerging Topics (mentioned but not yet saturated)")
if early:
    for kw in early:
        print(f"- **{kw.title()}** — early signal, potential content gap")
else:
    print("- No clear early-signal keywords extracted.")
print("\n---\n")

# ── Forge-ready data ───────────────────────────────────────────────────────

print("## Discussion Signal for The Forge\n")
print("This is live community signal from this week — what your audience is actually talking about, debating, and asking.")
print("Use this to make concepts timely and specific. If a topic appears in both the Pattern Report AND this discussion signal, prioritize it — that's a validated opportunity.\n")

print("### Top Discussed Topics")
for i, row in enumerate(reddit[:5], 1):
    title = short(row.get('title', ''), 90)
    sub = get_subreddit_name(row)
    sentiment = 'debate' if any(w in title.lower() for w in ['?', 'vs', 'versus', 'wrong', 'actually', 'myth']) else 'discussion'
    print(f"- {title} | r/{sub} | {sentiment}")
for i, row in enumerate(xposts[:3], 1):
    text = short(row.get('text', ''), 90)
    print(f"- {text} | X | signal")
for i, row in enumerate(hn[:3], 1):
    title = short(row.get('title', ''), 90)
    print(f"- {title} | HN | builder signal")
print("")

print("### Validated Overlap Topics (highest priority for The Forge)")
for kw in validated:
    print(f"- {kw.title()} | VALIDATED | Use a data-first operator angle tied to live workflow or market shift")
if not validated:
    print("- No high-confidence overlap topics extracted automatically.")
PY
}

# ── Config Loading ─────────────────────────────────────────────────────────────
mkdir -p "$WORKSPACE" "$OUTPUT_DIR"
CUTOFF_DATE="$(date_days_ago_utc "$VIRLO_LOOKBACK_DAYS")"

if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "No config found at $CONFIG_FILE"
  echo ""
  echo "Creating a sample config. Edit it and re-run."
  cat > "$CONFIG_FILE" << 'YAML'
niche: "AI Marketing"
virlo_comet_id: "YOUR_COMET_ID"
reddit_subreddits:
  - "artificial"
  - "marketing"
  - "aiautomation"
x_search_terms:
  - "ai marketing"
  - "vibe marketing"
YAML
  echo "Config saved to: $CONFIG_FILE"
  exit 0
fi

NICHE="${OVERRIDE_NICHE:-$(read_yaml_field "$CONFIG_FILE" "niche")}"
COMET_ID="${OVERRIDE_COMET:-$(read_yaml_field "$CONFIG_FILE" "virlo_comet_id")}"
SUBREDDITS="$(read_yaml_list "$CONFIG_FILE" "reddit_subreddits")"
X_TERMS="$(read_yaml_list "$CONFIG_FILE" "x_search_terms")"

if [[ -z "$NICHE" ]]; then
  echo "ERROR: 'niche' not set in config." >&2; exit 1
fi
if [[ -z "$COMET_ID" || "$COMET_ID" == "YOUR_COMET_ID" ]]; then
  echo "ERROR: 'virlo_comet_id' not configured. Run 'virlo.sh list' to get your comet ID." >&2; exit 1
fi

TODAY="$(date '+%Y-%m-%d')"
OUTPUT_FILE="$OUTPUT_DIR/briefing-${TODAY}.md"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M %Z')"

LAST30DAYS_SCRIPT="$(detect_last30days_script || true)"
LAST30DAYS_AVAILABLE=false
LAST30DAYS_MODE="none"
NORMALIZED_LAST30DAYS_SUMMARY=""
LAST30DAYS_JSON_FILE="$OUTPUT_DIR/last30days-${TODAY}.json"
LAST30DAYS_ERR_FILE="$OUTPUT_DIR/last30days-${TODAY}.err"
if [[ -n "$LAST30DAYS_SCRIPT" ]]; then
  echo "Pulling discussion signal via last30days..." >&2
  if [[ "$LAST30DAYS_SCRIPT" == *.py ]]; then
    LAST30DAYS_RUN=(python3 "$LAST30DAYS_SCRIPT")
  else
    LAST30DAYS_RUN=("$LAST30DAYS_SCRIPT")
  fi
  if "${LAST30DAYS_RUN[@]}" "$NICHE" --quick --emit=json > "$LAST30DAYS_JSON_FILE" 2> "$LAST30DAYS_ERR_FILE"; then
    if python3 - "$LAST30DAYS_JSON_FILE" <<'PY'
import json, sys
with open(sys.argv[1]) as f:
    data = json.load(f)
count = len(data.get('reddit', [])) + len(data.get('x', []))
raise SystemExit(0 if count > 0 else 1)
PY
    then
      LAST30DAYS_AVAILABLE=true
      LAST30DAYS_MODE="json"
    elif [[ -s "$LAST30DAYS_JSON_FILE" ]]; then
      NORMALIZED_LAST30DAYS_SUMMARY="$(normalize_last30days_summary "$(cat "$LAST30DAYS_JSON_FILE")")"
      if [[ -n "$NORMALIZED_LAST30DAYS_SUMMARY" ]]; then
        LAST30DAYS_AVAILABLE=true
        LAST30DAYS_MODE="text"
      fi
    fi
  fi
fi

# ── Virlo Data Pull ────────────────────────────────────────────────────────────
VIRLO_AVAILABLE=false
VIRLO_VIDEOS_RAW=""
VIRLO_OUTLIERS_RAW=""

if [[ -f "$VIRLO_SCRIPT" ]]; then
  echo "Pulling Virlo data for comet: $COMET_ID..." >&2

  if VIRLO_VIDEOS_RAW="$("$VIRLO_SCRIPT" videos "$COMET_ID" \
      --limit "$TOP_VIDEOS" \
      --order-by views \
      --sort desc 2>&1)"; then
    VIRLO_AVAILABLE=true
  else
    echo "WARN: Virlo videos call failed. Check your VIRLO_API_KEY and comet ID." >&2
  fi

  if $VIRLO_AVAILABLE; then
    if ! VIRLO_OUTLIERS_RAW="$("$VIRLO_SCRIPT" outliers "$COMET_ID" \
        --limit "$TOP_OUTLIERS" \
        --order-by outlier_ratio 2>&1)"; then
      echo "WARN: Virlo outliers call failed." >&2
      VIRLO_OUTLIERS_RAW=""
    fi
  fi
else
  echo "WARN: Virlo script not found at $VIRLO_SCRIPT" >&2
  echo "      Install the virlo skill or set up virlo.sh manually." >&2
fi

# ── Parse Virlo Output ─────────────────────────────────────────────────────────
# Virlo returns JSON. Parse with jq if available, else fall back to raw text.
parse_virlo_videos() {
  local raw="$1"
  if command -v jq &>/dev/null && echo "$raw" | jq . &>/dev/null 2>&1; then
    # JSON path: extract structured fields with URLs
    CUTOFF_DATE="$CUTOFF_DATE" echo "$raw" | jq -r '
      .data.videos // .data // .videos // . |
      if type == "array" then .[] else . end |
      select(((.publish_date // .published_at // .publishDate // .created_at // "")[0:10]) >= env.CUTOFF_DATE) |
      "- **\(.description // .title // "Untitled" | .[0:80])** | \(.views // .view_count // 0) views | \(.type // .platform // "unknown") | @\(.author.username // .creator.username // .creator_name // "unknown") | published \((.publish_date // .published_at // .publishDate // .created_at // "unknown")[0:10])\n  🔗 \(.url // "no URL available")"
    ' 2>/dev/null | head -$(( TOP_VIDEOS * 2 ))
  else
    # Fallback: return raw if not JSON
    echo "$raw" | head -20
  fi
}

parse_virlo_outliers() {
  local raw="$1"
  if command -v jq &>/dev/null && echo "$raw" | jq . &>/dev/null 2>&1; then
    CUTOFF_DATE="$CUTOFF_DATE" echo "$raw" | jq -r '
      .data.outliers // .data // .creators // . |
      if type == "array" then .[] else . end |
      select((.videos | map(select(((.publishDate // .publish_date // .published_at // .created_at // "")[0:10]) >= env.CUTOFF_DATE)) | length) > 0) |
      "- **@\(.creator.username // (.creator_url | split("@") | last | split("/") | first) // "Unknown")** | \(.follower_count // "?") followers | \(.outlier_ratio // "?")x average\n  🔗 Creator: \(.creator_url // "no URL")\n  Breakout: \((.videos | map(select(((.publishDate // .publish_date // .published_at // .created_at // "")[0:10]) >= env.CUTOFF_DATE)) | first | .description // .title // "N/A") | .[0:80]) (\((.videos | map(select(((.publishDate // .publish_date // .published_at // .created_at // "")[0:10]) >= env.CUTOFF_DATE)) | first | .views) // 0) views)\n  📅 Published: \(((.videos | map(select(((.publishDate // .publish_date // .published_at // .created_at // "")[0:10]) >= env.CUTOFF_DATE)) | first | .publishDate // .publish_date // .published_at // .created_at // "unknown")[0:10])\n  🔗 Video: \((.videos | map(select(((.publishDate // .publish_date // .published_at // .created_at // "")[0:10]) >= env.CUTOFF_DATE)) | first | .url) // "no URL")"
    ' 2>/dev/null | head -$(( TOP_OUTLIERS * 5 ))
  else
    echo "$raw" | head -15
  fi
}

# ── Build Search Queries for the Agent ────────────────────────────────────────
# The agent running this skill has web_search available.
# We emit a structured SEARCH DIRECTIVE that the agent must act on.
# Format: ##SEARCH_DIRECTIVE## so the agent can parse and execute it.

build_search_directives() {
  local subreddits="$1"
  local x_terms="$2"
  local niche="$3"

  echo ""
  echo "##SEARCH_DIRECTIVE_START##"
  echo ""
  echo "The agent reading this output MUST perform the following web searches"
  echo "to complete the 'What's Being DISCUSSED' section of the briefing."
  echo ""
  echo "### Reddit Searches"
  echo "For each subreddit below, search: site:reddit.com/r/[SUB] [NICHE] - recent posts"
  echo ""

  IFS=',' read -ra SUBS <<< "$subreddits"
  local i=1
  for sub in "${SUBS[@]}"; do
    sub="${sub#"${sub%%[![:space:]]*}"}"  # ltrim
    sub="${sub%"${sub##*[![:space:]]}"}"  # rtrim
    echo "${i}. SEARCH: site:reddit.com/r/${sub} ${niche}"
    echo "   GOAL: Find top threads from the last 30 days. Extract: theme, pain point, or question. Note subreddit and engagement signals (upvotes/comments if shown)."
    i=$((i+1))
  done

  echo ""
  echo "### X (Twitter) Searches"
  echo "For each term below, search X for recent conversations."
  echo ""

  IFS=',' read -ra TERMS <<< "$x_terms"
  local j=1
  for term in "${TERMS[@]}"; do
    term="${term#"${term%%[![:space:]]*}"}"
    term="${term%"${term##*[![:space:]]}"}"
    echo "${j}. SEARCH: site:x.com \"${term}\" OR site:twitter.com \"${term}\""
    echo "   GOAL: Find what practitioners are saying. Extract: topic, sentiment, notable accounts."
    j=$((j+1))
  done

  echo ""
  echo "### Additional Niche Search"
  echo "1. SEARCH: \"${niche}\" trending content creators 2025 OR 2026"
  echo "   GOAL: Identify any topics or formats gaining momentum not captured above."
  echo ""
  echo "##SEARCH_DIRECTIVE_END##"
  echo ""
  echo "After completing these searches, fill in the"
  echo "'## What's Being DISCUSSED' section in the briefing below."
  echo ""
}

# ── Assemble Briefing ──────────────────────────────────────────────────────────
{
cat << HEADER
# Niche Briefing: ${NICHE}
Generated: ${TIMESTAMP}

> This briefing fuses two signal types: **performance data** (what is getting views)
> and **discussion data** (what your audience is talking about).
> The Pattern Analysis section shows where they overlap.

---

HEADER

# --- VIRLO SECTION ---
echo "## What's PERFORMING (Virlo)"
echo ""

if $VIRLO_AVAILABLE && [[ -n "$VIRLO_VIDEOS_RAW" ]]; then
  echo "### Top Content This Week"
  echo ""
  PARSED_VIDEOS="$(parse_virlo_videos "$VIRLO_VIDEOS_RAW")"
  if [[ -n "$PARSED_VIDEOS" ]]; then
    echo "$PARSED_VIDEOS"
  else
    echo "_Could not parse Virlo video data. Raw output stored in $OUTPUT_DIR/virlo-raw-${TODAY}.txt_"
    echo "$VIRLO_VIDEOS_RAW" > "$OUTPUT_DIR/virlo-raw-${TODAY}.txt"
  fi
  echo ""

  echo "### Breakout Creators (Outlier Detection)"
  echo ""
  if [[ -n "$VIRLO_OUTLIERS_RAW" ]]; then
    PARSED_OUTLIERS="$(parse_virlo_outliers "$VIRLO_OUTLIERS_RAW")"
    if [[ -n "$PARSED_OUTLIERS" ]]; then
      echo "$PARSED_OUTLIERS"
    else
      echo "_No outlier data parsed._"
    fi
  else
    echo "_No outlier data available for this comet._"
  fi
  echo ""
else
  cat << VIRLO_MISSING
> Virlo data unavailable. Possible reasons:
> - Comet ID not set or incorrect
> - VIRLO_API_KEY not configured
> - Virlo script not installed (expected: $VIRLO_SCRIPT)
> - New comet has not completed its first collection run yet
>
> To install the Virlo skill: load the virlo skill in OpenClaw.
> To check your comets: run \`virlo.sh list\`

VIRLO_MISSING
fi

echo "---"
echo ""

if [[ "$LAST30DAYS_AVAILABLE" == true ]]; then
  if [[ "$LAST30DAYS_MODE" == "text" ]]; then
    echo "## What's Being DISCUSSED (Reddit + X)"
    echo ""
    printf '%s\n' "$NORMALIZED_LAST30DAYS_SUMMARY"
  else
    render_last30days_sections "$LAST30DAYS_JSON_FILE" "$NICHE"
  fi
  echo ""
  echo "---"
  echo ""
else
  # --- SEARCH DIRECTIVE ---
  build_search_directives "$SUBREDDITS" "$X_TERMS" "$NICHE"

  echo "---"
  echo ""

  # --- DISCUSSION SECTION (agent fills this in) ---
  cat << DISCUSSION_TEMPLATE
## What's Being DISCUSSED (Reddit + X)

> AGENT: Fill in this section after completing the searches above.
> Use the format below. Be specific: real thread titles, real quotes, real subreddits.

### Reddit Themes

| # | Theme | Subreddit | Summary |
|---|-------|-----------|---------|
| 1 | _[theme from search]_ | r/_[subreddit]_ | _[1-sentence summary of what people are saying]_ |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

### X Conversations

| # | Topic | Summary |
|---|-------|---------|
| 1 | _[search term or topic]_ | _[what practitioners are saying, notable accounts, sentiment]_ |
| 2 | | |
| 3 | | |

---

DISCUSSION_TEMPLATE

  # --- PATTERN ANALYSIS ---
  cat << PATTERN_TEMPLATE
## Pattern Analysis

> AGENT: After filling in both sections above, complete this analysis.
> This is the most valuable section. Think carefully before writing.

### Overlap (Validated Opportunities)
Topics that appear in BOTH the Virlo performance data AND Reddit/X discussions.
These have the strongest signal: the market wants them AND content is performing.

- _[topic]: performing on [platform], being discussed in [subreddit/X context]_
- _[topic]: ..._

### Early Signals (Performing but Not Discussed Yet)
Topics showing up in Virlo data but NOT in Reddit/X discussions.
Opportunity: you could be one of the first voices in the conversation.

- _[topic]: [views] views on [platform], minimal community discussion found_
- _[topic]: ..._

### Format Gaps (Discussed but Not Performing Yet)
Topics actively being discussed in Reddit/X but NOT showing up as high-performing content.
Opportunity: the audience wants this content but nobody has cracked the format.

- _[topic]: active in r/[sub], [X context], but no high-view content found_
- _[topic]: ..._

---

PATTERN_TEMPLATE

  # --- FORGE FEED ---
  cat << FORGE_TEMPLATE
## Raw Data for The Forge

> Copy this block directly into The Forge skill for content generation.
> Each line is one potential content piece with the key signal that validates it.

FORGE_TOPICS_START

Niche: ${NICHE}
Date: ${TODAY}

Top Performing Topics (from Virlo):
AGENT: Extract the top 5 topic themes from the Virlo video titles above.
Format each as: [topic] | [views] views | [platform] | [hook angle from title] | [URL]

Top Discussed Topics (from Reddit + X):
AGENT: Extract the top 5 topics from the Reddit/X searches.
Format each as: [topic] | [platform] | [emotion/angle: pain/curiosity/debate]

Validated Overlap Topics (highest priority):
AGENT: List topics that appeared in both signals.
Format each as: [topic] | VALIDATED | [specific angle to use]

---

### Content DNA Breakdown (per outlier video)

AGENT: For each outlier video listed in the Virlo section above, perform a
7-dimension Content DNA analysis. If the video description provides enough
context to reverse-engineer the content, fill all 7 dimensions. If the video
is visual-first (demo, reaction content, tutorial with minimal description),
FLAG it for manual review with the URL.

Per outlier, output this table:

**@[creator] — [video title snippet]**
🔗 [video URL]

| Dimension | Analysis |
|-----------|----------|
| 1. Topic | What the video is about (core subject) |
| 2. Angle | What makes this take unique (contrarian, insider, underdog, debate, etc.) |
| 3. Hook Structure | First-line pattern (question, shocking stat, story open, challenge, confession) |
| 4. Story Structure | Content flow (problem-solution, listicle, narrative arc, before-after, A/B test, debate) |
| 5. Visual Format | Talking head, text overlay, screen recording, B-roll, split screen, etc. |
| 6. Key Visuals | Props, settings, graphics, on-screen text, thumbnails |
| 7. Audio | Music, voiceover, natural sound, trending audio, silence |

If visual-first (description too sparse to fully analyze):
> ⚠️ VISUAL-FIRST: Watch first 30 sec → [URL]
> Answer: What visual hook grabs attention? Production style? Replicable format?

FORGE_TOPICS_END

---

FORGE_TEMPLATE
fi

cat << METADATA
## Metadata

| Field | Value |
|-------|-------|
| Niche | ${NICHE} |
| Virlo Comet | ${COMET_ID} |
| Subreddits | ${SUBREDDITS} |
| X Terms | ${X_TERMS} |
| Generated | ${TIMESTAMP} |
| Output | ${OUTPUT_FILE} |
| Discussion Signal | $( [[ "$LAST30DAYS_AVAILABLE" == true ]] && echo "last30days" || echo "search directives / agent fill" ) |

METADATA

} > "$OUTPUT_FILE"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "Content Radar complete."
echo ""
echo "Briefing saved to:"
echo "  $OUTPUT_FILE"
echo ""
if [[ "$LAST30DAYS_AVAILABLE" == true ]]; then
  echo "Discussion signal source:"
  echo "  last30days ($LAST30DAYS_SCRIPT)"
  echo ""
  echo "Next steps:"
  echo "  1. Review the completed briefing."
  echo "  2. Feed it into The Forge or Monday Drop."
else
  echo "Next steps:"
  echo "  1. The briefing contains SEARCH_DIRECTIVE blocks."
  echo "     The OpenClaw agent reading this output should perform those searches now."
  echo "  2. After searches, fill in the 'What's Being DISCUSSED' section."
  echo "  3. Complete the 'Pattern Analysis' section."
  echo "  4. Copy 'Raw Data for The Forge' into The Forge skill."
fi

echo ""
echo "Read the briefing:"
echo "  cat \"$OUTPUT_FILE\""
