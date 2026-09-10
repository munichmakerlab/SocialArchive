# MuMaLab Social Archive

Zentrales, plattformunabhängiges Archiv der Munich-Maker-Lab-Social-Media-Posts
(Mastodon, Tumblr, Instagram, Twitter/X, Bluesky, ...). Ziel: die Historie
unabhängig von den externen Plattformen dauerhaft sichern und als
`posts.json`/RSS bereitstellen.

## Stand

Aktuell nur ein PoC (siehe [`FINDINGS.md`](FINDINGS.md)): pro Plattform wurde
geprüft, welche Tools/APIs ohne Login welche Rohdaten liefern.

```
poc/
├── mastodon_fetch.py    # native Mastodon API
├── bluesky_fetch.py     # public AT-Proto AppView API
├── tumblr_fetch.py      # legacy /api/read/json + gallery-dl Vergleich
├── instagram_fetch.py   # Instaloader + gallery-dl (beide ohne Login blockiert)
├── twitter_fetch.py     # gallery-dl (ohne Login blockiert)
└── raw/<platform>/      # unveränderte Roh-Beispiele je Plattform
```

## Setup

Dependencies and the `.venv` are managed with [uv](https://docs.astral.sh/uv/)
(`pyproject.toml` + `uv.lock`).

```bash
uv sync                          # creates/updates .venv from uv.lock
uv run poc/<platform>_fetch.py   # runs a script inside that .venv

uv add <package>                 # add a new dependency
```

Normalizer, Dedup, `posts.json`-Generator und GitHub-Action-Sync folgen erst,
nachdem die PoC-Ergebnisse aus `FINDINGS.md` in ein gemeinsames Schema
überführt wurden.
