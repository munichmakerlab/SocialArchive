"""Minimal, dependency-free HTML -> plain text conversion.

Good enough for short social media post bodies; not a general HTML parser.
"""

import html
import re

_TAG_RE = re.compile(r"<[^>]+>")
_BLOCK_BREAK_RE = re.compile(r"</(p|br|div|li)\s*>", re.IGNORECASE)


def html_to_text(fragment: str) -> str:
    with_breaks = _BLOCK_BREAK_RE.sub("\n", fragment)
    text = _TAG_RE.sub("", with_breaks)
    return html.unescape(text).strip()
