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

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python poc/<platform>_fetch.py
```

Normalizer, Dedup, `posts.json`-Generator und GitHub-Action-Sync folgen erst,
nachdem die PoC-Ergebnisse aus `FINDINGS.md` in ein gemeinsames Schema
überführt wurden.
