"""PoC: fetch one real post from the old MuMaLab Tumblr blog.

Tries Tumblr's legacy, key-free `/api/read/json` endpoint first (works
directly on the custom domain, no registration needed), then falls back to
gallery-dl for comparison. gallery-dl's tumblr extractor only recognizes
*.tumblr.com URLs (not the custom domain) and uses a shared anonymous OAuth
key that is globally rate-limited across all gallery-dl users -- both are
notable findings in their own right and are captured verbatim either way.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import httpx

GALLERY_DL = [sys.executable, "-m", "gallery_dl"]
CUSTOM_DOMAIN = "https://log.munichmakerlab.de"
TUMBLR_SUBDOMAIN_URL = "https://munichmakerlab.tumblr.com"
RAW_DIR = Path(__file__).parent / "raw" / "tumblr"

JSONP_RE = re.compile(r"^\s*var tumblr_api_read\s*=\s*(.*?);\s*$", re.DOTALL)


def try_legacy_api() -> bool:
    client = httpx.Client(timeout=15, headers={"User-Agent": "mumalab-archive-poc/0.1"})
    resp = client.get(f"{CUSTOM_DOMAIN}/api/read/json", params={"num": 1})
    resp.raise_for_status()

    match = JSONP_RE.match(resp.text)
    if not match:
        (RAW_DIR / "legacy_api_raw.txt").write_text(resp.text)
        print("Tumblr legacy API: response was not the expected JSONP wrapper")
        return False

    data = json.loads(match.group(1))
    post = data["posts"][0]

    out_path = RAW_DIR / f"legacy_api_{post['id']}.json"
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    print("Tumblr fetch via legacy /api/read/json OK (no API key needed)")
    print(f"  saved: {out_path}")
    print(f"  url: {post.get('url')}")
    print(f"  date: {post.get('date')}")
    print(f"  type: {post.get('type')}")
    print(f"  blog total posts available: {data.get('posts-total')}")
    return True


def try_gallery_dl() -> bool:
    result = subprocess.run(
        [*GALLERY_DL, "-j", "--no-download", TUMBLR_SUBDOMAIN_URL],
        capture_output=True,
        text=True,
        timeout=60,
    )
    (RAW_DIR / "gallery-dl_stderr.txt").write_text(result.stderr)

    if result.returncode != 0 or not result.stdout.strip():
        print("Tumblr fetch via gallery-dl FAILED")
        print(f"  returncode: {result.returncode}")
        print(f"  stderr (see raw/tumblr/gallery-dl_stderr.txt): {result.stderr[:300]}")
        return False

    try:
        entries = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        (RAW_DIR / "gallery-dl_stdout_raw.txt").write_text(result.stdout)
        print(f"Tumblr fetch: gallery-dl output was not valid JSON ({exc})")
        return False

    out_path = RAW_DIR / "gallery-dl_output.json"
    out_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False))

    first = entries[0] if entries else None
    first_dict = first[-1] if isinstance(first, list) else first
    if isinstance(first_dict, dict) and "error" in first_dict:
        print("Tumblr fetch via gallery-dl BLOCKED (extractor ran, but returned an error entry)")
        print(f"  saved: {out_path}")
        print(f"  error: {first_dict.get('error')}: {first_dict.get('message')}")
        return False

    print("Tumblr fetch via gallery-dl OK")
    print(f"  saved: {out_path}")
    print(f"  entries returned: {len(entries)}")
    return True


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ok_legacy = try_legacy_api()
    ok_gallery_dl = try_gallery_dl()

    if not ok_legacy and not ok_gallery_dl:
        print("Tumblr: both methods failed -- see raw/tumblr/*.txt")
        sys.exit(0)  # documented blocker, not a hard PoC failure


if __name__ == "__main__":
    main()
