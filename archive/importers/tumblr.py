"""Tumblr importer: legacy, key-free /api/read/json endpoint.

Found during the PoC to work directly against the custom domain without any
API registration -- unlike gallery-dl, which only recognizes *.tumblr.com
URLs and shares a rate-limited anonymous API key across all gallery-dl users.
"""

import json
import re

import httpx

from archive.paths import RAW_DIR

BLOG_URL = "https://log.munichmakerlab.de"

JSONP_RE = re.compile(r"^\s*var tumblr_api_read\s*=\s*(.*?);\s*$", re.DOTALL)


def run(limit: int = 20) -> list[str]:
    """Fetch the blog's latest posts and save each as raw/tumblr/<id>.json.

    Returns the list of post ids written.
    """
    out_dir = RAW_DIR / "tumblr"
    out_dir.mkdir(parents=True, exist_ok=True)

    client = httpx.Client(timeout=15, headers={"User-Agent": "mumalab-archive/0.1"})
    resp = client.get(f"{BLOG_URL}/api/read/json", params={"num": limit})
    resp.raise_for_status()

    match = JSONP_RE.match(resp.text)
    if not match:
        raise ValueError("unexpected response shape from Tumblr legacy API")

    data = json.loads(match.group(1))

    written = []
    for post in data["posts"]:
        (out_dir / f"{post['id']}.json").write_text(
            json.dumps(post, indent=2, ensure_ascii=False)
        )
        written.append(post["id"])
    return written


if __name__ == "__main__":
    ids = run()
    print(f"tumblr: wrote {len(ids)} raw posts")
