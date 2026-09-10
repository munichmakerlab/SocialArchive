# PoC Findings – Social Media Source Evaluation

Results of a PoC run against the real MuMaLab accounts (2026-09-10),
public access only, no login/cookies/tokens. Scripts: `poc/*_fetch.py`,
raw data: `poc/raw/<platform>/`.

## Summary

| Platform | Method | Result | Auth needed? |
|---|---|---|---|
| Mastodon | native REST API | ✅ full post incl. video attachment | No |
| Bluesky | public AT-Proto AppView API | ✅ full post incl. video embed | No |
| Tumblr | legacy `/api/read/json` | ✅ full post + blog-wide structure known | No |
| Tumblr | gallery-dl | ⚠️ blocked (shared rate limit) | Own API key needed |
| Instagram | Instaloader | ❌ 429 Too Many Requests | Yes (login/session) |
| Instagram | gallery-dl | ❌ returns only a placeholder, no real posts | Yes (login/session) |
| Twitter/X | gallery-dl | ❌ returns only a placeholder, no real tweets | Yes (login/session) |

## Mastodon

- Method: direct `httpx` call against `chaos.social`, no auth needed (`/api/v1/accounts/lookup`, then `/api/v1/accounts/{id}/statuses`).
- Example post: `poc/raw/mastodon/117240146027825683.json`
  - `url`: `https://chaos.social/@munichmakerlab/117240146027825683`
  - `content`: full HTML (1584 characters)
  - `media_attachments[0].type = "video"`, incl. `url` (mp4), `preview_url`, `meta.original.{width,height,duration,bitrate}` — video is fully recognized with technical metadata.
  - `tags`: 11 hashtags extracted cleanly.
- Conclusion: best source in the set. The native API is fully sufficient, no importer tool needed.

## Bluesky

- Method: `httpx` against the public AppView endpoint `public.api.bsky.app` (`app.bsky.feed.getAuthorFeed`), no auth/session needed.
- Example post: `poc/raw/bluesky/3mv34tlxuxk27.json`
  - Text under `post.record.text`, timestamp under `post.record.createdAt`.
  - The original URL has to be constructed from the `at://...` URI + handle (no direct `url` field like Mastodon has): `https://bsky.app/profile/<handle>/post/<rkey>`.
  - `post.embed.$type = "app.bsky.embed.video#view"` with `playlist` (HLS m3u8), `thumbnail`, `aspectRatio` — video is recognized, but comes as a streaming playlist, not a single MP4 file (relevant for "mirror media locally").
- Conclusion: second-best source. The native API is sufficient. Mirroring video requires resolving/downloading the HLS playlist separately (e.g. via `yt-dlp`, which supports m3u8).

## Tumblr

- **Legacy `/api/read/json`** (unauthenticated, directly on the custom domain `log.munichmakerlab.de`): works completely, no API key/registration needed.
  - Example post: `poc/raw/tumblr/legacy_api_767797918064345088.json` (type `regular`, plain text with HTML in `regular-body`, `tags`, `date`, `url`).
  - An additional sample (50 posts, not persisted) showed: `photo` posts with `photo-url-1280` fields, carousels as a `photos` array (each photo with its own `photo-url-*` resolutions), `video` posts with `video-source`/`video-player` fields. All three media types are fully reachable through the same API.
  - The blog has **340 posts** available in total, per `posts-total`.
- **gallery-dl**: only recognizes `*.tumblr.com` URLs, not the custom domain (`log.munichmakerlab.de` → `Unsupported URL`). Against `munichmakerlab.tumblr.com` it did run, but internally uses a shared/anonymous OAuth key that is rate-limited across all gallery-dl users platform-wide (`AbortExtraction: Rate limit will reset at 20:04:29`) — already exhausted on the very first test run.
- Conclusion: **the legacy JSON API is the better choice for Tumblr** over gallery-dl — no key needed, full field coverage, works directly against the custom domain.

## Instagram

- **Instaloader** (anonymous, `max_connection_attempts=1`): `ConnectionException: 429 Too Many Requests` on the very first profile lookup (`api/v1/users/web_profile_info`). See `poc/raw/instagram/instaloader_error.txt`.
- **gallery-dl** (`-j --no-download`): technically completed (return code 0), but returned only a single placeholder entry with the recognized target URL (`.../posts/`) and no real post metadata at all — see `poc/raw/instagram/gallery-dl_output.json`. So effectively blocked as well, just without an explicit error message.
- Conclusion: the hardest source in the set, as expected. Without login/session, not a single real post can currently be extracted. For the historical initial import, either an official Instagram data export or a session (cookies) via GitHub Secrets is needed, as already planned in the outline.

## Twitter/X

- **gallery-dl** (`-j --no-download`) against `https://twitter.com/munichmakerlab`: completed (return code 0), but likewise returned only a placeholder entry for the recognized timeline URL, no individual tweets — see `poc/raw/twitter/gallery-dl_stdout.txt`.
- No error text in stderr; the block only shows up as an empty result list.
- Conclusion: without cookies, no real tweets can be extracted. For the historical import, the official Twitter/X account data export remains the most realistic source, as planned (if access to the old account still exists).

## Raw JSON structure comparison (core fields)

| Field in the later schema | Mastodon | Bluesky | Tumblr (legacy API) |
|---|---|---|---|
| Original URL | `url` (present directly) | must be constructed from `uri` + handle | `url` (present directly) |
| Text/HTML | `content` (HTML) | `record.text` (plain text, no HTML) | `regular-body` (HTML) |
| Timestamp | `created_at` (ISO 8601) | `record.createdAt` (ISO 8601) | `date-gmt` (custom format) + `unix-timestamp` |
| Tags | `tags[].name` | (no structured tags in the sample post) | `tags[]` |
| Image media | `media_attachments[].type=image` | `embed.images[]` (on other post types) | `photo-url-*` / `photos[]` (carousel) |
| Video media | `media_attachments[].type=video` + direct MP4 URL | `embed` with HLS `playlist` (m3u8) | `video-source` / `video-player` |

## Open points for the next iteration

- **Instagram/Twitter**: no real posts reachable without login right now. Clarify official data exports for the initial import; for ongoing sync, possibly session cookies via GitHub Secrets (risk: account suspension, should be aligned with the team before implementing).
- **Tumblr**: use the legacy API as the primary source; gallery-dl at most as a fallback, and then with its own registered Tumblr API key (not gallery-dl's shared one).
- **Video normalization**: Bluesky only delivers video as an HLS playlist, not a single file — the planned media mirroring needs a resolution step for that (e.g. `yt-dlp`), Mastodon delivers a direct MP4 URL.

Schema, normalizer, `posts.json` generator and the GitHub Action have since
been built on top of these findings — see the main [`README.md`](README.md)
for the current pipeline and its known gaps.
