"""Per-source sync health tracking (data/state.json).

Tracks, per platform: whether the last sync attempt succeeded, when it last
*actually* succeeded (survives through failing runs -- that's the whole
point), how many posts are known, and how many were new in the last run.

A corrupt or missing state file must never break the build -- it just means
everything renders as "never synced" until the next successful sync.
"""

import json
from datetime import datetime, timezone

from archive.paths import DATA_DIR

STATE_PATH = DATA_DIR / "state.json"

ALL_PLATFORMS = ["mastodon", "bluesky", "tumblr", "instagram", "twitter"]
NOT_IMPLEMENTED = {
    "instagram": "blocked without login (see FINDINGS.md)",
    "twitter": "blocked without login (see FINDINGS.md)",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_state() -> dict:
    try:
        return json.loads(STATE_PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def record_success(state: dict, platform: str, *, new_count: int, known_count: int, warning: str | None = None) -> None:
    now = _now()
    state[platform] = {
        "status": "ok",
        "last_attempt": now,
        "last_success": now,
        "new_posts_last_run": new_count,
        "known_count": known_count,
        "error": None,
        "warning": warning,
    }


def record_failure(state: dict, platform: str, *, error: str) -> None:
    existing = state.get(platform, {})
    state[platform] = {
        **existing,
        "status": "error",
        "last_attempt": _now(),
        "error": error,
    }


def ensure_not_implemented_entries(state: dict) -> None:
    for platform, reason in NOT_IMPLEMENTED.items():
        if platform not in state:
            state[platform] = {
                "status": "not_implemented",
                "last_attempt": None,
                "last_success": None,
                "new_posts_last_run": None,
                "known_count": None,
                "error": None,
                "warning": None,
                "reason": reason,
            }
