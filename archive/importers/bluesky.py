"""Bluesky importer: public AT Protocol AppView API, no auth/session needed."""

import json

import httpx

from archive.paths import RAW_DIR

APPVIEW = "https://public.api.bsky.app"
HANDLE = "munichmakerlab.bsky.social"


def run(limit: int = 20) -> list[str]:
    """Fetch the account's latest posts and save each feed item as raw/bluesky/<rkey>.json.

    Returns the list of rkeys written.
    """
    out_dir = RAW_DIR / "bluesky"
    out_dir.mkdir(parents=True, exist_ok=True)

    client = httpx.Client(timeout=15, headers={"User-Agent": "mumalab-archive/0.1"})
    resp = client.get(
        f"{APPVIEW}/xrpc/app.bsky.feed.getAuthorFeed",
        params={"actor": HANDLE, "limit": limit, "filter": "posts_no_replies"},
    )
    resp.raise_for_status()

    written = []
    for item in resp.json().get("feed", []):
        uri = item["post"]["uri"]
        rkey = uri.rsplit("/", 1)[-1]
        (out_dir / f"{rkey}.json").write_text(json.dumps(item, indent=2, ensure_ascii=False))
        written.append(rkey)
    return written


if __name__ == "__main__":
    rkeys = run()
    print(f"bluesky: wrote {len(rkeys)} raw posts")
