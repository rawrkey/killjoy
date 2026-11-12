---
author: BytesAgain
category: general
description: Generate CSS and SVG animation code snippets using bash and Python. Use when building UI animations, keyframes, or transition effects.
homepage: https://bytesagain.com
metadata:
    github-path: animation
    github-ref: refs/heads/main
    github-repo: https://github.com/bytesagain/ai-skills
    github-tree-sha: 650d7653bfb0412ed214a1ec86ee915932ae01cf
name: animation
source: https://github.com/bytesagain/ai-skills
tags:
    - animation
    - general
    - cli
    - tool
version: 1.0.0
---
# animation

Generate CSS and SVG animation code snippets using bash and Python. Use when building UI animations, keyframes, or transition effects.

## Commands

### `status`

```bash
scripts/script.sh status
```

Show current status

### `add`

```bash
scripts/script.sh add
```

Add new entry

### `list`

```bash
scripts/script.sh list
```

List all entries

### `search`

```bash
scripts/script.sh search
```

Search entries

### `remove`

```bash
scripts/script.sh remove
```

Remove entry by number

### `export`

```bash
scripts/script.sh export
```

Export data to file

### `stats`

```bash
scripts/script.sh stats
```

Show statistics

### `config`

```bash
scripts/script.sh config
```

View or set config

### `help`

```bash
scripts/script.sh help
```

### `version`

```bash
scripts/script.sh version
```

## Configuration

Use `scripts/script.sh config <key> <value>` to set preferences.

| Variable | Required | Description |
|----------|----------|-------------|
| `ANIMATION_DIR` | No | Data directory (default: ~/.animation/) |

## Data Storage

All data stored in `~/.animation/` using JSONL format (one JSON object per line).

## Output

Structured output to stdout. Exit code 0 on success, 1 on error.

---

*Powered by BytesAgain | bytesagain.com | hello@bytesagain.com*
