"""PoC: fetch one real public post from the MuMaLab Bluesky account via the
public AT Protocol AppView API (no auth/session needed for public data)."""

import json
import sys
from pathlib import Path

import httpx

APPVIEW = "https://public.api.bsky.app"
HANDLE = "munichmakerlab.bsky.social"
RAW_DIR = Path(__file__).parent / "raw" / "bluesky"


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    client = httpx.Client(timeout=15, headers={"User-Agent": "mumalab-archive-poc/0.1"})

    resp = client.get(
        f"{APPVIEW}/xrpc/app.bsky.feed.getAuthorFeed",
        params={"actor": HANDLE, "limit": 1, "filter": "posts_no_replies"},
    )
    resp.raise_for_status()
    feed = resp.json().get("feed", [])

    if not feed:
        print("ERROR: no posts returned", file=sys.stderr)
        sys.exit(1)

    item = feed[0]
    post = item["post"]
    record = post.get("record", {})

    uri = post["uri"]  # at://did:plc:xxx/app.bsky.feed.post/<rkey>
    rkey = uri.rsplit("/", 1)[-1]
    original_url = f"https://bsky.app/profile/{HANDLE}/post/{rkey}"

    out_path = RAW_DIR / f"{rkey}.json"
    out_path.write_text(json.dumps(item, indent=2, ensure_ascii=False))

    embed = post.get("embed", {})
    print("Bluesky fetch OK")
    print(f"  saved: {out_path}")
    print(f"  url: {original_url}")
    print(f"  created_at: {record.get('createdAt')}")
    print(f"  text: {record.get('text', '')[:80]!r}")
    print(f"  embed type: {embed.get('$type')}")


if __name__ == "__main__":
    main()
