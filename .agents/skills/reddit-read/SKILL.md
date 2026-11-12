---
description: Zero-setup Reddit reader via public JSON API. No auth, no install - just curl + python3. Read subreddits, threads with comments, search posts. Use when user says "read reddit", "reddit posts", "check subreddit", "reddit thread", "reddit search", or needs to read public Reddit content without rdcli setup.
metadata:
    github-path: reddit-read
    github-ref: refs/heads/main
    github-repo: https://github.com/DisposableByDefault/the-skill-vault
    github-tree-sha: d7303e2816cd1deaac292b637f7f3ad9dd2ec820
name: reddit-read
---
# reddit-read

Read Reddit using the public `.json` API. Zero dependencies - just `curl` + `python3` (pre-installed everywhere).

**No auth needed.** Append `.json` to any Reddit URL. Works for all public content.

**When to use this vs rdcli:** Use this for reading/searching public content with zero setup. Use rdcli when you need to post, vote, message, or access private subreddits.

## Critical Rules

1. **Always save to disk first, parse later.** Never pipe curl directly into python for multi-request workflows. Download JSON files, then parse offline. This survives rate limits and lets you re-parse without re-fetching.
2. **Always use random sleep between requests.** Reddit rate-limits aggressively (~30 req/min). Even 2-3 fast sequential requests can trigger a block that returns empty HTML instead of JSON. Use `sleep $((RANDOM % 3 + 3))` (3-5s random) between every request.
3. **Never use inline `python3 -c` for multi-line scripts.** Bash escaping of `!=`, f-strings with `{}`, and backslashes breaks constantly. Write a temp `.py` file once, reuse it.
4. **One request at a time.** Never fire parallel curl calls to Reddit. Serial + sleep only.

## Setup (Run Once Per Session)

```bash
# 1. User agent - MUST be full browser string, short UAs get 403
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

# 2. Working directory for downloaded JSON
mkdir -p /tmp/reddit

# 3. Listing parser (subreddit posts)
cat > /tmp/reddit/parse_listing.py << 'PYEOF'
import json, sys
data = json.load(sys.stdin)
for i, p in enumerate(data['data']['children'], 1):
    d = p['data']
    title = d['title'][:120]
    print(f"{i}. [{d['score']}pts|{d['num_comments']}c] {title}")
    print(f"   u/{d['author']} | {d['name']}")
    print(f"   https://reddit.com{d['permalink']}")
    print()
PYEOF

# 4. Thread + comments parser
cat > /tmp/reddit/parse_thread.py << 'PYEOF'
import json, sys

def print_comments(children, depth=0):
    for c in children:
        if c['kind'] != 't1':
            continue
        x = c['data']
        body = x['body'][:300].replace('\n', ' ')
        indent = '  ' * depth
        prefix = '|' if depth else ''
        print(f"{indent}{prefix}[{x['score']}pts] u/{x['author']}: {body}")
        print()
        if x.get('replies') and isinstance(x['replies'], dict):
            print_comments(x['replies']['data']['children'], depth + 1)

data = json.load(sys.stdin)
p = data[0]['data']['children'][0]['data']
print(f"=== {p['title']} ===")
print(f"u/{p['author']} | {p['score']}pts | {p['num_comments']}c")
if p.get('selftext'):
    print()
    print(p['selftext'][:800])
print()
print('--- Comments ---')
print()
print_comments(data[1]['data']['children'])
PYEOF
```

## Commands

### Read Subreddit Posts (Listing)

```bash
curl -s -A "$UA" "https://www.reddit.com/r/SUBREDDIT/top.json?t=week&limit=25" \
  -o /tmp/reddit/listing.json
python3 /tmp/reddit/parse_listing.py < /tmp/reddit/listing.json
```

Sort options in URL path: `hot`, `new`, `top`, `rising`, `controversial`
Time filter for top/controversial: `?t=hour|day|week|month|year|all`

### Read Single Thread + Comments

```bash
sleep $((RANDOM % 3 + 3))
curl -s -A "$UA" "https://www.reddit.com/r/SUB/comments/ID.json?sort=top&limit=25" \
  -o /tmp/reddit/thread_ID.json
python3 /tmp/reddit/parse_thread.py < /tmp/reddit/thread_ID.json
```

Comment sort: `top`, `best`, `new`, `controversial`, `old`, `qa`

### Bulk Download Multiple Threads

Use this when you need to read 3+ threads (e.g. analyzing pain points, researching a topic). Download all first, parse all after.

```bash
# Extract thread IDs from listing (after downloading listing.json)
# Then download each with random sleep
for id in ID1 ID2 ID3 ID4 ID5; do
  sleep $((RANDOM % 3 + 3))
  echo "Fetching $id..."
  curl -s -A "$UA" \
    "https://www.reddit.com/r/SUBREDDIT/comments/${id}.json?sort=top&limit=25" \
    -o "/tmp/reddit/thread_${id}.json"
  sz=$(wc -c < "/tmp/reddit/thread_${id}.json")
  echo "  -> ${sz} bytes"
done

# Then parse all offline (no network, no rate limits)
for id in ID1 ID2 ID3 ID4 ID5; do
  echo ""; echo "========================================"; echo ""
  python3 /tmp/reddit/parse_thread.py < "/tmp/reddit/thread_${id}.json"
done
```

### Search

```bash
# Search within a subreddit
curl -s -A "$UA" \
  "https://www.reddit.com/r/SUBREDDIT/search.json?q=QUERY&restrict_sr=on&sort=relevance&t=all&limit=10" \
  -o /tmp/reddit/search.json
python3 /tmp/reddit/parse_listing.py < /tmp/reddit/search.json

# Search all of Reddit - same parser, different URL
curl -s -A "$UA" \
  "https://www.reddit.com/search.json?q=QUERY&sort=relevance&t=all&limit=10" \
  -o /tmp/reddit/search_all.json
python3 /tmp/reddit/parse_listing.py < /tmp/reddit/search_all.json
```

Search sort: `relevance`, `hot`, `top`, `new`, `comments`

## Example: Pain Point Analysis (One-Shot)

Full workflow to find user pain points from a subreddit in one pass:

```bash
# 1. Setup (parsers + UA)
# [run the Setup section above]

# 2. Get top posts for the week
curl -s -A "$UA" "https://www.reddit.com/r/SUBREDDIT/top.json?t=week&limit=25" \
  -o /tmp/reddit/listing.json
python3 /tmp/reddit/parse_listing.py < /tmp/reddit/listing.json

# 3. Pick thread IDs that look like pain/frustration/help posts
#    (questions, complaints, "how do I", "struggling with", "help")

# 4. Bulk download with sleep
for id in ID1 ID2 ID3 ID4 ID5; do
  sleep $((RANDOM % 3 + 3))
  curl -s -A "$UA" \
    "https://www.reddit.com/r/SUBREDDIT/comments/${id}.json?sort=top&limit=25" \
    -o "/tmp/reddit/thread_${id}.json"
  echo "Fetched $id ($(wc -c < /tmp/reddit/thread_${id}.json) bytes)"
done

# 5. Parse all offline
for id in ID1 ID2 ID3 ID4 ID5; do
  echo ""; echo "========================================"; echo ""
  python3 /tmp/reddit/parse_thread.py < "/tmp/reddit/thread_${id}.json"
done

# 6. Synthesize pain points with exact quotes from the output
```

## Rate Limits & Troubleshooting

- ~30 req/min unauthenticated, but bursts of 3+ fast requests reliably trigger blocks
- **Symptom of rate limit:** curl returns HTML (not JSON), python3 throws `JSONDecodeError: Expecting value: line 1 column 1`
- **Fix:** wait 10-15 seconds, then resume with `sleep $((RANDOM % 3 + 3))` between requests
- **Do NOT use old.reddit.com as fallback** - it blocks even more aggressively
- Downloaded JSON in `/tmp/reddit/` survives rate limits - just re-parse without re-fetching

## Limitations

**Read-only.** No posting, voting, messaging, or private subreddits. For write operations, use rdcli skill instead.
