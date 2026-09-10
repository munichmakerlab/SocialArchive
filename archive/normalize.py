"""Convert raw/<platform>/*.json into canonical Post objects.

One raw source post = one canonical Post for now. Cross-platform
deduplication/merging (e.g. the same content posted to Mastodon and
Bluesky) is not implemented yet -- see FINDINGS.md / README for next steps.

A single malformed/unexpected raw post must never abort the whole build:
each file is normalized independently and failures are logged and skipped.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from archive.htmlutil import html_to_text
from archive.models import Media, Post, Source
from archive.paths import RAW_DIR

_VIDEO_SRC_RE = re.compile(r'src="([^"]+\.(?:mp4|webm)[^"]*)"')


def normalize_mastodon(raw: dict) -> Post:
    html_content = raw.get("content", "")
    media = []
    for attachment in raw.get("media_attachments", []):
        kind = {"image": "image", "video": "video", "gifv": "gif"}.get(attachment["type"])
        if kind is None:  # e.g. "audio", "unknown" -- not modeled yet
            continue
        media.append(
            Media(
                type=kind,
                url=attachment["url"],
                original_url=attachment["url"],
                alt=attachment.get("description"),
            )
        )

    published_at = datetime.fromisoformat(raw["created_at"].replace("Z", "+00:00"))
    updated_at = published_at
    if raw.get("edited_at"):
        updated_at = datetime.fromisoformat(raw["edited_at"].replace("Z", "+00:00"))

    return Post(
        id=f"mastodon-{raw['id']}",
        published_at=published_at,
        updated_at=updated_at,
        text=html_to_text(html_content),
        html=html_content,
        sources=[Source(platform="mastodon", id=str(raw["id"]), url=raw["url"])],
        media=media,
        tags=[t["name"] for t in raw.get("tags", [])],
    )


def normalize_bluesky(raw: dict) -> Post:
    post = raw["post"]
    record = post["record"]
    author_handle = post["author"]["handle"]
    rkey = post["uri"].rsplit("/", 1)[-1]
    original_url = f"https://bsky.app/profile/{author_handle}/post/{rkey}"

    text = record.get("text", "")
    html_content = "".join(f"<p>{line}</p>" for line in text.splitlines() if line.strip())

    media = []
    embed = post.get("embed") or {}
    embed_type = embed.get("$type", "")
    if embed_type == "app.bsky.embed.images#view":
        for image in embed.get("images", []):
            media.append(
                Media(
                    type="image",
                    url=image["fullsize"],
                    original_url=image["fullsize"],
                    alt=image.get("alt") or None,
                )
            )
    elif embed_type == "app.bsky.embed.video#view":
        # served as an HLS playlist (.m3u8), not a single file -- mirroring
        # this will need an extra resolution step (e.g. yt-dlp), not a
        # plain download. Keep the playlist URL as the reference for now.
        media.append(
            Media(type="video", url=embed["playlist"], original_url=embed["playlist"])
        )

    published_at = datetime.fromisoformat(record["createdAt"].replace("Z", "+00:00"))

    return Post(
        id=f"bluesky-{rkey}",
        published_at=published_at,
        updated_at=published_at,
        text=text,
        html=html_content,
        sources=[Source(platform="bluesky", id=rkey, url=original_url)],
        media=media,
        tags=[],
    )


def normalize_tumblr(raw: dict) -> Post:
    post_type = raw["type"]
    tags = raw.get("tags", [])
    published_at = datetime.fromtimestamp(raw["unix-timestamp"], tz=timezone.utc)

    media: list[Media] = []
    if post_type == "regular":
        title = raw.get("regular-title") or ""
        body = raw.get("regular-body") or ""
        html_content = f"<h1>{title}</h1>{body}" if title else body
    elif post_type == "photo":
        caption = raw.get("photo-caption") or ""
        html_content = caption
        photos = raw.get("photos") or [raw]
        for photo in photos:
            url = photo.get("photo-url-1280") or photo.get("photo-url-500")
            if url:
                media.append(Media(type="image", url=url, original_url=url))
    elif post_type == "video":
        caption = raw.get("video-caption") or ""
        html_content = caption
        match = _VIDEO_SRC_RE.search(raw.get("video-player", "") or "")
        if match:
            url = match.group(1)
            media.append(Media(type="video", url=url, original_url=url))
        # else: externally embedded video (e.g. YouTube) -- no direct file
        # to mirror, text/caption is still preserved above.
    else:
        # quote/link/chat/audio/answer etc. -- not modeled in detail yet,
        # fall back to whatever caption-ish field exists so the post is at
        # least captured with its URL/date/tags rather than dropped.
        html_content = next(
            (raw[k] for k in ("caption", "chat-body", "quote-text") if raw.get(k)), ""
        )

    return Post(
        id=f"tumblr-{raw['id']}",
        published_at=published_at,
        updated_at=published_at,
        text=html_to_text(html_content),
        html=html_content,
        sources=[Source(platform="tumblr", id=str(raw["id"]), url=raw["url"])],
        media=media,
        tags=tags,
    )


_NORMALIZERS = {
    "mastodon": normalize_mastodon,
    "bluesky": normalize_bluesky,
    "tumblr": normalize_tumblr,
}


def normalize_all(raw_dir: Path = RAW_DIR) -> list[Post]:
    posts: list[Post] = []
    for platform, normalizer in _NORMALIZERS.items():
        platform_dir = raw_dir / platform
        if not platform_dir.is_dir():
            continue
        for path in sorted(platform_dir.glob("*.json")):
            try:
                raw = json.loads(path.read_text())
                posts.append(normalizer(raw))
            except Exception as exc:  # noqa: BLE001 -- one bad file must not abort the build
                print(f"WARNING: failed to normalize {path}: {type(exc).__name__}: {exc}")
    return posts
