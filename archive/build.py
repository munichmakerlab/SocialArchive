"""Normalize raw/* into data/posts.json and generate the public/ outputs."""

import json
from collections import Counter

from archive.feed import build_feed_xml
from archive.models import Post
from archive.normalize import normalize_all
from archive.paths import DATA_DIR, PUBLIC_DIR, RAW_DIR

LATEST_COUNT = 20


def _posts_json(posts: list[Post]) -> str:
    return json.dumps(
        [p.model_dump(mode="json") for p in posts], indent=2, ensure_ascii=False
    )


def run() -> list[Post]:
    posts = normalize_all()
    posts.sort(key=lambda p: p.published_at, reverse=True)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    posts_json = _posts_json(posts)
    (DATA_DIR / "posts.json").write_text(posts_json)
    (PUBLIC_DIR / "posts.json").write_text(posts_json)
    (PUBLIC_DIR / "latest.json").write_text(_posts_json(posts[:LATEST_COUNT]))
    (PUBLIC_DIR / "feed.xml").write_text(build_feed_xml(posts))

    return posts


def print_report(posts: list[Post]) -> None:
    per_source = Counter(s.platform for p in posts for s in p.sources)
    print("MuMaLab Social Archive Build\n")
    for platform in sorted(per_source):
        print(f"{platform.capitalize()}\n  {per_source[platform]} posts")
    print(f"\nArchive\n  {len(posts)} canonical posts")
    print(f"  {sum(len(p.media) for p in posts)} media references")
    print(
        "\nNote: no cross-platform deduplication yet -- 1 raw source post = "
        "1 canonical post. Instagram/Twitter not included (blocked without login)."
    )


if __name__ == "__main__":
    result = run()
    print_report(result)
