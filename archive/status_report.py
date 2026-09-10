"""Render the per-source sync health state as a markdown table and inject it
into README.md between marker comments.
"""

from pathlib import Path

from archive.paths import ROOT
from archive.state import ALL_PLATFORMS, NOT_IMPLEMENTED

STATUS_START = "<!-- STATUS:START -->"
STATUS_END = "<!-- STATUS:END -->"

_LABELS = {
    "mastodon": "Mastodon",
    "bluesky": "Bluesky",
    "tumblr": "Tumblr",
    "instagram": "Instagram",
    "twitter": "Twitter/X",
}


def _status_symbol(entry: dict) -> str:
    if entry.get("status") == "not_implemented":
        return "⛔"
    if entry.get("status") == "error":
        return "❌"
    if entry.get("status") == "ok" and entry.get("warning"):
        return "⚠️"
    if entry.get("status") == "ok":
        return "✅"
    return "❔"  # never attempted, but not marked not_implemented either


def _last_success_cell(entry: dict) -> str:
    last_success = entry.get("last_success")
    if not last_success:
        return "never"
    return last_success.replace("T", " ").split(".")[0].split("+")[0] + " UTC"


def _new_posts_cell(entry: dict) -> str:
    new_count = entry.get("new_posts_last_run")
    if new_count is None:
        return "–"
    return f"+{new_count}"


def _known_posts_cell(entry: dict) -> str:
    known_count = entry.get("known_count")
    return "–" if known_count is None else str(known_count)


def render_status_table(state: dict) -> str:
    platforms = [p for p in ALL_PLATFORMS]
    entries = {p: state.get(p, {"status": "not_implemented" if p in NOT_IMPLEMENTED else "never"}) for p in platforms}

    header = "| | " + " | ".join(_LABELS[p] for p in platforms) + " |"
    separator = "|---|" + "---|" * len(platforms)
    status_row = "| Status | " + " | ".join(_status_symbol(entries[p]) for p in platforms) + " |"
    last_success_row = "| Last successful sync (UTC) | " + " | ".join(
        _last_success_cell(entries[p]) for p in platforms
    ) + " |"
    new_posts_row = "| New posts (last run) | " + " | ".join(_new_posts_cell(entries[p]) for p in platforms) + " |"
    known_row = "| Known posts | " + " | ".join(_known_posts_cell(entries[p]) for p in platforms) + " |"

    return "\n".join([header, separator, status_row, last_success_row, new_posts_row, known_row])


def update_readme_status(table_markdown: str, readme_path: Path = ROOT / "README.md") -> None:
    text = readme_path.read_text()
    start = text.find(STATUS_START)
    end = text.find(STATUS_END)

    if start == -1 or end == -1 or end < start:
        print(f"WARNING: status markers not found in {readme_path}, skipping README update")
        return

    new_text = (
        text[: start + len(STATUS_START)]
        + "\n"
        + table_markdown
        + "\n"
        + text[end:]
    )
    readme_path.write_text(new_text)
