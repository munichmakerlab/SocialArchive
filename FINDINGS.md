# PoC Findings – Social Media Source Evaluation

Ergebnisse eines PoC-Durchlaufs gegen die echten MuMaLab-Accounts (2026-09-10),
rein öffentlicher Zugriff ohne Login/Cookies/Tokens. Scripts: `poc/*_fetch.py`,
Rohdaten: `poc/raw/<platform>/`.

## Zusammenfassung

| Plattform | Methode | Ergebnis | Auth nötig? |
|---|---|---|---|
| Mastodon | native REST API | ✅ voller Post inkl. Video-Attachment | Nein |
| Bluesky | public AT-Proto AppView API | ✅ voller Post inkl. Video-Embed | Nein |
| Tumblr | legacy `/api/read/json` | ✅ voller Post + Blog-weite Struktur bekannt | Nein |
| Tumblr | gallery-dl | ⚠️ blockiert (geteiltes Rate-Limit) | Eigener API-Key nötig |
| Instagram | Instaloader | ❌ 429 Too Many Requests | Ja (Login/Session) |
| Instagram | gallery-dl | ❌ liefert nur Platzhalter, keine echten Posts | Ja (Login/Session) |
| Twitter/X | gallery-dl | ❌ liefert nur Platzhalter, keine echten Tweets | Ja (Login/Session) |

## Mastodon

- Methode: direkter `httpx`-Call gegen `chaos.social`, kein Auth nötig (`/api/v1/accounts/lookup`, dann `/api/v1/accounts/{id}/statuses`).
- Beispielpost: `poc/raw/mastodon/117240146027825683.json`
  - `url`: `https://chaos.social/@munichmakerlab/117240146027825683`
  - `content`: vollständiges HTML (1584 Zeichen)
  - `media_attachments[0].type = "video"`, inkl. `url` (mp4), `preview_url`, `meta.original.{width,height,duration,bitrate}` — Video wird also vollständig mit technischen Metadaten erkannt.
  - `tags`: 11 Hashtags sauber extrahiert.
- Fazit: beste Quelle im Set. Native API reicht komplett aus, kein Importer-Tool nötig.

## Bluesky

- Methode: `httpx` gegen den public AppView-Endpoint `public.api.bsky.app` (`app.bsky.feed.getAuthorFeed`), kein Auth/Session nötig.
- Beispielpost: `poc/raw/bluesky/3mv34tlxuxk27.json`
  - Text unter `post.record.text`, Timestamp unter `post.record.createdAt`.
  - Original-URL muss selbst aus `at://...` URI + Handle konstruiert werden (kein direktes `url`-Feld wie bei Mastodon): `https://bsky.app/profile/<handle>/post/<rkey>`.
  - `post.embed.$type = "app.bsky.embed.video#view"` mit `playlist` (HLS m3u8), `thumbnail`, `aspectRatio` — Video wird erkannt, liegt aber als Streaming-Playlist vor, nicht als einzelne MP4-Datei (relevant für "Medien lokal spiegeln").
- Fazit: zweitbeste Quelle. Native API reicht aus. Für Video-Spiegelung muss die HLS-Playlist separat aufgelöst/heruntergeladen werden (z. B. via `yt-dlp`, das m3u8 unterstützt).

## Tumblr

- **Legacy `/api/read/json`** (unauthentifiziert, direkt auf der Custom Domain `log.munichmakerlab.de`): funktioniert vollständig, kein API-Key/Registrierung nötig.
  - Beispielpost: `poc/raw/tumblr/legacy_api_767797918064345088.json` (Typ `regular`, reiner Text mit HTML in `regular-body`, `tags`, `date`, `url`).
  - Zusätzliche Stichprobe (50 Posts, nicht dauerhaft gespeichert) zeigte: `photo`-Posts mit `photo-url-1280`-Feldern, Carousels als `photos`-Array (je Foto eigene `photo-url-*`-Auflösungen), `video`-Posts mit `video-source`/`video-player`-Feldern. Alle drei Medientypen sind über dieselbe API vollständig erreichbar.
  - Blog hat laut `posts-total` insgesamt **340 Posts** verfügbar.
- **gallery-dl**: erkennt nur `*.tumblr.com`-URLs, nicht die Custom Domain (`log.munichmakerlab.de` → `Unsupported URL`). Gegen `munichmakerlab.tumblr.com` lief es an, nutzt aber intern einen geteilten/anonymen OAuth-Key, der plattformweit über alle gallery-dl-Nutzer hinweg rate-limitiert ist (`AbortExtraction: Rate limit will reset at 20:04:29`) — bereits beim ersten Testlauf erschöpft.
- Fazit: **die legacy JSON-API ist für Tumblr die bessere Wahl** als gallery-dl — kein Key nötig, volle Feldabdeckung, funktioniert direkt gegen die Custom Domain.

## Instagram

- **Instaloader** (anonym, `max_connection_attempts=1`): `ConnectionException: 429 Too Many Requests` beim allerersten Profil-Lookup (`api/v1/users/web_profile_info`). Siehe `poc/raw/instagram/instaloader_error.txt`.
- **gallery-dl** (`-j --no-download`): lief technisch durch (Returncode 0), lieferte aber nur einen einzigen Platzhalter-Eintrag mit der erkannten Ziel-URL (`.../posts/`) und keinerlei echten Post-Metadaten — siehe `poc/raw/instagram/gallery-dl_output.json`. Faktisch also ebenfalls blockiert, nur ohne explizite Fehlermeldung.
- Fazit: wie erwartet die schwierigste Quelle. Ohne Login/Session ist aktuell kein einziger echter Post extrahierbar. Für den historischen Initialimport sind entweder ein offizieller Instagram-Datenexport oder eine Session (Cookies) über GitHub Secrets nötig, wie im Grobkonzept vorgesehen.

## Twitter/X

- **gallery-dl** (`-j --no-download`) gegen `https://twitter.com/munichmakerlab`: lief durch (Returncode 0), lieferte aber ebenfalls nur einen Platzhalter-Eintrag für die erkannte Timeline-URL, keine einzelnen Tweets — siehe `poc/raw/twitter/gallery-dl_stdout.txt`.
- Kein Fehlertext in stderr; die Blockade äußert sich nur als leere Ergebnisliste.
- Fazit: ohne Cookies keine echten Tweets extrahierbar. Für den historischen Import bleibt, wie geplant, der offizielle Twitter/X-Account-Datenexport die realistischste Quelle (falls noch Zugriff auf den alten Account besteht).

## Raw-JSON-Strukturvergleich (Kernfelder)

| Feld im späteren Schema | Mastodon | Bluesky | Tumblr (legacy API) |
|---|---|---|---|
| Original-URL | `url` (direkt vorhanden) | selbst konstruieren aus `uri` + Handle | `url` (direkt vorhanden) |
| Text/HTML | `content` (HTML) | `record.text` (Plaintext, kein HTML) | `regular-body` (HTML) |
| Timestamp | `created_at` (ISO 8601) | `record.createdAt` (ISO 8601) | `date-gmt` (custom Format) + `unix-timestamp` |
| Tags | `tags[].name` | (keine strukturierten Tags im Sample-Post) | `tags[]` |
| Bild-Medien | `media_attachments[].type=image` | `embed.images[]` (in anderen Post-Typen) | `photo-url-*` / `photos[]` (Carousel) |
| Video-Medien | `media_attachments[].type=video` + direkte MP4-URL | `embed` mit HLS-`playlist` (m3u8) | `video-source` / `video-player` |

## Offene Punkte für die nächste Iteration

- **Instagram/Twitter**: ohne Login aktuell keine echten Posts erreichbar. Für Initialimport offizielle Datenexporte klären; für laufenden Sync ggf. Session-Cookies über GitHub Secrets (Risiko: Account-Sperrung, sollte mit dem Team abgestimmt werden, bevor das umgesetzt wird).
- **Tumblr**: legacy API als Primärquelle nutzen; gallery-dl höchstens als Fallback, und dann mit eigenem registriertem Tumblr-API-Key (nicht dem geteilten von gallery-dl).
- **Video-Normalisierung**: Bluesky liefert Video nur als HLS-Playlist, nicht als einzelne Datei — die geplante Medien-Spiegelung braucht dafür einen Auflösungsschritt (z. B. `yt-dlp`), Mastodon liefert direkt eine MP4-URL.
- Schema/Normalizer/`posts.json`-Generator/GitHub Action sind bewusst noch nicht gebaut — das folgt erst nach Review dieses Dokuments.
