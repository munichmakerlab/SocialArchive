"""CLI: `python -m archive sync` fetches raw data, `python -m archive build`
normalizes it into data/posts.json + public/*.

A single broken importer must not abort the others or damage previously
fetched raw data -- each importer runs independently and failures are
reported as warnings.
"""

import sys

from archive.importers import bluesky, mastodon, tumblr
from archive.paths import RAW_DIR
from archive.state import ensure_not_implemented_entries, load_state, record_failure, record_success, save_state

IMPORTERS = {"mastodon": mastodon, "bluesky": bluesky, "tumblr": tumblr}


def sync() -> None:
    state = load_state()

    for name, module in IMPORTERS.items():
        raw_dir = RAW_DIR / name
        existing_before = {p.stem for p in raw_dir.glob("*.json")} if raw_dir.is_dir() else set()

        try:
            written = module.run()
        except Exception as exc:  # noqa: BLE001 -- one broken source must not stop the sync
            print(f"WARNING: {name} importer failed: {type(exc).__name__}: {exc}")
            record_failure(state, name, error=f"{type(exc).__name__}: {exc}")
            continue

        new_count = len(set(written) - existing_before)
        known_count = len(list(raw_dir.glob("*.json"))) if raw_dir.is_dir() else len(written)

        warning = None
        if not written and existing_before:
            warning = f"returned 0 posts, {len(existing_before)} were previously known"
            print(f"WARNING: {name} importer appears broken -- {warning}. Existing archive preserved.")

        record_success(state, name, new_count=new_count, known_count=known_count, warning=warning)
        print(f"{name}: wrote {len(written)} raw posts (+{new_count} new, {known_count} known)")

    ensure_not_implemented_entries(state)
    save_state(state)


def build() -> None:
    from archive.build import print_report, run

    posts, mirror_stats = run()
    print_report(posts, mirror_stats)


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("sync", "build"):
        print("usage: python -m archive [sync|build]", file=sys.stderr)
        sys.exit(1)

    {"sync": sync, "build": build}[sys.argv[1]]()


if __name__ == "__main__":
    main()
