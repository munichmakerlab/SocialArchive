# MuMaLab Social Archive

Zentrales, plattformunabhängiges Archiv der Munich-Maker-Lab-Social-Media-Posts
(Mastodon, Tumblr, Instagram, Twitter/X, Bluesky, ...). Ziel: die Historie
unabhängig von den externen Plattformen dauerhaft sichern und als
`posts.json`/RSS bereitstellen.

## Stand

Erste End-to-End-Pipeline für die drei Quellen, die ohne Login funktionieren
(Mastodon, Bluesky, Tumblr):

```
external platform -> archive/importers/*.py -> raw/<platform>/*.json
                                                      |
                                             archive/normalize.py
                                                      v
                                       data/posts.json (kanonisch)
                                                      |
                              archive/build.py -> public/{posts,latest}.json, feed.xml
```

```bash
uv run python -m archive sync   # fetch raw posts from each source into raw/
uv run python -m archive build  # normalize raw/ -> data/posts.json + public/*
```

Instagram und Twitter/X haben (noch) keinen Importer: der PoC hat gezeigt,
dass ohne Login/Session aktuell keine echten Posts erreichbar sind (siehe
[`FINDINGS.md`](FINDINGS.md)).

**Bewusste Lücken in diesem Stand:**
- Keine Cross-Platform-Deduplizierung: ein Raw-Post = ein kanonischer Post.
  Crossposts (z. B. derselbe Inhalt auf Mastodon und Bluesky) erscheinen
  aktuell noch als zwei separate Einträge.
- Kein `state.json`/inkrementeller Sync: `sync` holt jedes Mal die letzten
  20 Posts pro Plattform neu, es gibt noch keinen "nur neue Posts"-Modus.
- Medien werden noch nicht lokal gespiegelt, `media.url` zeigt aktuell auf
  die Original-CDN-URLs der Plattformen.
- `.github/workflows/sync.yml` existiert, wurde aber noch nicht in einem
  echten Repo/Actions-Lauf getestet.

## Projektstruktur

```
archive/
├── importers/{mastodon,bluesky,tumblr}.py  # fetch -> raw/<platform>/*.json
├── models.py       # kanonisches Post-Schema (pydantic)
├── normalize.py     # raw/*.json -> Post
├── feed.py          # RSS 2.0 Generator
└── build.py          # normalize_all() -> data/posts.json + public/*

raw/<platform>/       # unveränderte Rohdaten je Plattform
data/posts.json       # generierter, kanonischer Datenbestand
public/               # statischer Output (posts.json, latest.json, feed.xml)

poc/                  # eingefrorenes PoC-Experiment, siehe FINDINGS.md
```

## Setup

Dependencies und `.venv` werden mit [uv](https://docs.astral.sh/uv/) verwaltet
(`pyproject.toml` + `uv.lock`).

```bash
uv sync              # erstellt/aktualisiert .venv aus uv.lock
uv run <script.py>   # führt ein Script im .venv aus
uv add <package>      # neue Abhängigkeit hinzufügen
```
