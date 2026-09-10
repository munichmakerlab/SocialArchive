# MuMaLab Social Archive

Central, platform-independent archive of Munich Maker Lab's social media posts
(Mastodon, Tumblr, Instagram, Twitter/X, Bluesky, ...). Goal: preserve the
history independently of the external platforms and serve it as
`posts.json`/RSS.

## Status

First end-to-end pipeline for the three sources that work without login
(Mastodon, Bluesky, Tumblr):

```
external platform -> archive/importers/*.py -> raw/<platform>/*.json
                                                      |
                                             archive/normalize.py
                                                      v
                                       data/posts.json (canonical)
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
- No cross-platform deduplication: one raw post = one canonical post.
  Crossposts (e.g. the same content on Mastodon and Bluesky) currently still
  show up as two separate entries.
- No `state.json`/incremental sync: `sync` re-fetches the latest 20 posts per
  platform every time, there is no "new posts only" mode yet.
- Media is not mirrored locally yet; `media.url` currently points at the
  platforms' original CDN URLs.

## Project structure

```
archive/
├── importers/{mastodon,bluesky,tumblr}.py  # fetch -> raw/<platform>/*.json
├── models.py       # canonical Post schema (pydantic)
├── normalize.py     # raw/*.json -> Post
├── feed.py          # RSS 2.0 generator
└── build.py          # normalize_all() -> data/posts.json + public/*

raw/<platform>/       # unmodified raw data per platform
data/posts.json       # generated, canonical data set
public/               # static output (posts.json, latest.json, feed.xml)

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
