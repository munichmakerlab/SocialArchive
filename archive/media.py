"""Mirror post images into the repo itself (`public/media/<post-id>/`).

The platform's original CDN URL is kept on `Media.original_url` -- only
`Media.url` is rewritten to point at the repo-hosted copy. A single failed
download must never abort the whole build: it's logged as a warning and that
one media entry just keeps pointing at its original external URL.

This is deliberately a thin wrapper around local-filesystem storage so a
future S3/R2/MinIO backend can implement the same interface (store one
image, return its public URL) without touching normalize.py/build.py.
"""

from pathlib import Path
from urllib.parse import urlsplit

import httpx

from archive.models import Post
from archive.paths import PUBLIC_BASE_URL, PUBLIC_DIR

_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
_DEFAULT_EXTENSION = ".jpg"


def _guess_extension(url: str) -> str:
    suffix = Path(urlsplit(url).path).suffix.lower()
    return suffix if suffix in _ALLOWED_EXTENSIONS else _DEFAULT_EXTENSION


class LocalMediaStore:
    """Stores mirrored images under public/media/<post-id>/ in the repo."""

    def __init__(self, base_dir: Path = PUBLIC_DIR / "media", public_base_url: str = PUBLIC_BASE_URL):
        self.base_dir = base_dir
        self.public_base_url = public_base_url

    def store(self, client: httpx.Client, source_url: str, post_id: str, index: int) -> tuple[str, bool]:
        """Download source_url if not already mirrored.

        Returns (public_url, was_downloaded).
        """
        ext = _guess_extension(source_url)
        filename = f"{index:02d}{ext}"
        dest_dir = self.base_dir / post_id
        dest_path = dest_dir / filename

        if dest_path.exists():
            return f"{self.public_base_url}/media/{post_id}/{filename}", False

        resp = client.get(source_url, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(resp.content)

        return f"{self.public_base_url}/media/{post_id}/{filename}", True


def mirror_images(posts: list[Post], store: LocalMediaStore | None = None) -> tuple[int, int, int]:
    """Mirror every image Media of every post in place.

    Returns (newly_downloaded, already_present, failed).
    """
    store = store or LocalMediaStore()
    client = httpx.Client(headers={"User-Agent": "mumalab-archive/0.1"})

    downloaded = 0
    skipped = 0
    failed = 0
    for post in posts:
        for index, media in enumerate(post.media):
            if media.type != "image":
                continue
            try:
                media.url, was_downloaded = store.store(
                    client, media.original_url or media.url, post.id, index
                )
                downloaded += was_downloaded
                skipped += not was_downloaded
            except Exception as exc:  # noqa: BLE001 -- one broken image must not abort the build
                print(f"WARNING: failed to mirror image for {post.id} #{index}: {type(exc).__name__}: {exc}")
                failed += 1

    return downloaded, skipped, failed
