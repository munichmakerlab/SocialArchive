"""PoC: fetch one real public status from the MuMaLab Mastodon account via the
native Mastodon REST API (no auth needed for public data)."""

import json
import sys
from pathlib import Path

import httpx

INSTANCE = "https://chaos.social"
ACCOUNT = "munichmakerlab"
RAW_DIR = Path(__file__).parent / "raw" / "mastodon"


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    client = httpx.Client(timeout=15, headers={"User-Agent": "mumalab-archive-poc/0.1"})

    lookup = client.get(f"{INSTANCE}/api/v1/accounts/lookup", params={"acct": ACCOUNT})
    lookup.raise_for_status()
    account_id = lookup.json()["id"]

    statuses = client.get(
        f"{INSTANCE}/api/v1/accounts/{account_id}/statuses",
        params={"limit": 1, "exclude_reblogs": "true", "exclude_replies": "true"},
    )
    statuses.raise_for_status()
    posts = statuses.json()

    if not posts:
        print("WARNING: account has no non-reblog/non-reply statuses, retrying without excludes")
        statuses = client.get(
            f"{INSTANCE}/api/v1/accounts/{account_id}/statuses", params={"limit": 1}
        )
        statuses.raise_for_status()
        posts = statuses.json()

    if not posts:
        print("ERROR: no statuses returned at all", file=sys.stderr)
        sys.exit(1)

    post = posts[0]
    out_path = RAW_DIR / f"{post['id']}.json"
    out_path.write_text(json.dumps(post, indent=2, ensure_ascii=False))

    media = post.get("media_attachments", [])
    print("Mastodon fetch OK")
    print(f"  saved: {out_path}")
    print(f"  url: {post.get('url')}")
    print(f"  created_at: {post.get('created_at')}")
    print(f"  text length (content html): {len(post.get('content', ''))}")
    print(f"  media count: {len(media)} ({[m.get('type') for m in media]})")
    print(f"  tags: {[t.get('name') for t in post.get('tags', [])]}")


if __name__ == "__main__":
    main()
