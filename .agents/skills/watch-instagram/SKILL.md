---
name: watch-instagram
description: Watch, inspect, download, and analyze any Instagram Reel, Instagram Post (photo, video, or multi-slide carousel), or profile link. Extracts audio transcripts, keyframe image snapshots, on-screen text via OCR, and produces structured breakdowns. Use whenever the user shares an Instagram Reel or Post link or asks to analyze/watch an Instagram URL.
---

# Watch Instagram (Reels & Posts)

Use this skill whenever the user shares an Instagram link (`instagram.com/reel/...`, `instagram.com/p/...`, `instagram.com/reels/...`, `instagram.com/tv/...`).

## Execution

Run the built-in ingestion engine:

```bash
python .agents/skills/reel-watch/scripts/reel.py "<instagram-url>"
```

### Supported Media Types:
- **Reels (`/reel/` or `/reels/`)**: Downloads video, extracts audio via Faster-Whisper, samples keyframes, and runs OCR on on-screen text.
- **Posts (`/p/`)**:
  - Single photo posts
  - Single video posts
  - Multi-slide Carousels (downloads all slides—both images and video slides—and extracts captions).
- **Local files**: Works with local `.mp4`, `.mov`, `.jpg`, `.png`, and carousel folders.

Output lands in `reels/<shortcode>/` with:
- `manifest.json`: Full timeline, timestamps, transcripts, and OCR data.
- `frames/`: Extracted visual frames.
- `local.md`: Complete written breakdown of everything shown and spoken.

