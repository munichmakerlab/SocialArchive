"""Mastodon importer: native REST API, no auth needed for public data."""

import json

import httpx

from archive.paths import RAW_DIR

INSTANCE = "https://chaos.social"
ACCOUNT = "munichmakerlab"


def run(limit: int = 20) -> list[str]:
    """Fetch the account's latest public statuses and save each as raw/mastodon/<id>.json.

    Returns the list of status ids written.
    """
    out_dir = RAW_DIR / "mastodon"
    out_dir.mkdir(parents=True, exist_ok=True)

    client = httpx.Client(timeout=15, headers={"User-Agent": "mumalab-archive/0.1"})

    lookup = client.get(f"{INSTANCE}/api/v1/accounts/lookup", params={"acct": ACCOUNT})
    lookup.raise_for_status()
    account_id = lookup.json()["id"]

    statuses = client.get(
        f"{INSTANCE}/api/v1/accounts/{account_id}/statuses",
        params={"limit": limit, "exclude_reblogs": "true"},
    )
    statuses.raise_for_status()

    written = []
    for post in statuses.json():
        (out_dir / f"{post['id']}.json").write_text(
            json.dumps(post, indent=2, ensure_ascii=False)
        )
        written.append(post["id"])
    return written


if __name__ == "__main__":
    ids = run()
    print(f"mastodon: wrote {len(ids)} raw posts")
