"""CLI: `python -m archive sync` fetches raw data, `python -m archive build`
normalizes it into data/posts.json + public/*.

A single broken importer must not abort the others or damage previously
fetched raw data -- each importer runs independently and failures are
reported as warnings.
"""

import sys

from archive.importers import bluesky, mastodon, tumblr

IMPORTERS = {"mastodon": mastodon, "bluesky": bluesky, "tumblr": tumblr}


def sync() -> None:
    for name, module in IMPORTERS.items():
        try:
            written = module.run()
            print(f"{name}: wrote {len(written)} raw posts")
        except Exception as exc:  # noqa: BLE001 -- one broken source must not stop the sync
            print(f"WARNING: {name} importer failed: {type(exc).__name__}: {exc}")


def build() -> None:
    from archive.build import print_report, run

    print_report(run())


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("sync", "build"):
        print("usage: python -m archive [sync|build]", file=sys.stderr)
        sys.exit(1)

    {"sync": sync, "build": build}[sys.argv[1]]()


if __name__ == "__main__":
    main()
