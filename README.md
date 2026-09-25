# MuMaLab Social Archive

Central, platform-independent archive of Munich Maker Lab's social media posts
(Mastodon, Tumblr, Instagram, Twitter/X, Bluesky, ...). Goal: preserve the
history independently of the external platforms and serve it as
`posts.json`/RSS.

## Source status

<!-- STATUS:START -->
| | Mastodon | Bluesky | Tumblr | Instagram | Twitter/X |
|---|---|---|---|---|---|
| Status | ✅ | ✅ | ✅ | ⛔ | ⛔ |
| Last successful sync (UTC) | 2026-09-25 08:50:14 UTC | 2026-09-25 08:50:14 UTC | 2026-09-25 08:50:15 UTC | never | never |
| New posts (last run) | +0 | +0 | +0 | – | – |
| Known posts | 24 | 24 | 20 | – | – |
<!-- STATUS:END -->

A source erroring or going quiet never deletes previously-archived posts --
importers only ever write raw files, never remove them -- and the "Last
successful sync" timestamp above keeps showing the last time a source
*actually* worked even while it's currently failing.

## Status

First end-to-end pipeline for the three sources that work without login
(Mastodon, Bluesky, Tumblr):

```
external platform -> archive/importers/*.py -> raw/<platform>/*.json
                                                      |
                                             archive/normalize.py
                                                      |
                                            archive/deduplicate.py
                                                      v
                                       data/posts.json (canonical, deduped)
                                                      |
                              archive/build.py -> public/{posts,latest}.json, feed.xml
```

```bash
uv run python -m archive sync   # fetch raw posts from each source into raw/
uv run python -m archive build  # normalize raw/ -> data/posts.json + public/*
```

Instagram and Twitter/X don't have an importer yet: the PoC showed that no
real posts are reachable without login/session on either platform right now
(see [`FINDINGS.md`](FINDINGS.md)).

The `sync.yml` GitHub Actions workflow has been triggered manually against the
real repo and confirmed working (fetch, normalize, build, auto-commit).

**Known gaps at this stage:**
- Cross-platform deduplication (`archive/deduplicate.py`) merges posts that
  were cross-posted within a 6-hour window and score >=80 on normalized
  text similarity (`rapidfuzz` token-set ratio), preferring Mastodon as the
  canonical source, then Bluesky, then Tumblr. A post reworded very
  differently per platform, or one with no matching text at all (e.g. an
  image-only crosspost), won't be caught -- that would need image-hash or
  semantic matching, not implemented yet.
- `data/state.json` now tracks per-source sync health (see "Source status"
  above), but there's still no `last_seen_id`-based incremental fetch:
  `sync` re-fetches the latest 20 posts per platform every time.
- Images are mirrored into `public/media/<post-id>/`; `media.url` points at
  the repo-hosted copy and `media.original_url` keeps the platform's CDN URL.
  Video is not mirrored yet (Bluesky serves it as an HLS playlist, Mastodon
  as a direct MP4 -- both still just link out to the original URL).

## Project structure

```
archive/
├── importers/{mastodon,bluesky,tumblr}.py  # fetch -> raw/<platform>/*.json
├── models.py       # canonical Post schema (pydantic)
├── normalize.py     # raw/*.json -> Post
├── deduplicate.py    # merges cross-platform duplicate Posts (Mastodon > Bluesky > Tumblr)
├── media.py          # mirrors post images into public/media/<post-id>/
├── feed.py          # RSS 2.0 generator
└── build.py          # normalize_all() -> deduplicate() -> mirror_images() -> data/posts.json + public/*

raw/<platform>/       # unmodified raw data per platform
data/posts.json       # generated, canonical data set
public/               # static output (posts.json, latest.json, feed.xml, media/)

poc/                  # frozen PoC experiment, see FINDINGS.md
```

## Setup

Dependencies and the `.venv` are managed with [uv](https://docs.astral.sh/uv/)
(`pyproject.toml` + `uv.lock`).

```bash
uv sync              # creates/updates .venv from uv.lock
uv run <script.py>   # runs a script inside the .venv
uv add <package>      # add a new dependency
```
