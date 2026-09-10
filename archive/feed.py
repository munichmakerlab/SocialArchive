"""Minimal hand-written RSS 2.0 generator (no external feed library dependency)."""

from datetime import datetime, timezone
from xml.sax.saxutils import escape

from archive.models import Post
from archive.paths import PUBLIC_BASE_URL

FEED_TITLE = "Munich Maker Lab -- Social Archive"
FEED_LINK = f"{PUBLIC_BASE_URL}/"
FEED_SELF_URL = f"{PUBLIC_BASE_URL}/feed.xml"
FEED_DESCRIPTION = "Archived posts from all MuMaLab social media accounts."

_TITLE_MAX_LEN = 80


def _rfc822(dt: datetime) -> str:
    return dt.strftime("%a, %d %b %Y %H:%M:%S %z")


def _cdata(html: str) -> str:
    # a literal "]]>" would otherwise terminate the CDATA block early
    return html.replace("]]>", "]]]]><![CDATA[>")


def _item_title(text: str) -> str:
    text = " ".join(text.split())
    if not text:
        return "(untitled post)"
    if len(text) <= _TITLE_MAX_LEN:
        return text
    truncated = text[:_TITLE_MAX_LEN].rsplit(" ", 1)[0]
    return f"{truncated}…"


def build_feed_xml(posts: list[Post]) -> str:
    items = []
    for post in posts:
        primary_url = post.sources[0].url if post.sources else FEED_LINK
        enclosures = "".join(
            f'<enclosure url="{escape(m.url)}" type="{"video/mp4" if m.type == "video" else "image/jpeg"}"/>'
            for m in post.media
        )
        categories = "".join(f"<category>{escape(tag)}</category>" for tag in post.tags)
        items.append(
            f"""  <item>
    <title>{escape(_item_title(post.text))}</title>
    <guid isPermaLink="false">{escape(post.id)}</guid>
    <link>{escape(primary_url)}</link>
    <pubDate>{_rfc822(post.published_at)}</pubDate>
    <description><![CDATA[{_cdata(post.html)}]]></description>
    {categories}
    {enclosures}
  </item>"""
        )

    items_xml = "\n".join(items)
    last_build_date = _rfc822(datetime.now(timezone.utc))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>{escape(FEED_TITLE)}</title>
  <link>{escape(FEED_LINK)}</link>
  <atom:link href="{escape(FEED_SELF_URL)}" rel="self" type="application/rss+xml"/>
  <description>{escape(FEED_DESCRIPTION)}</description>
  <language>en-us</language>
  <lastBuildDate>{last_build_date}</lastBuildDate>
{items_xml}
</channel>
</rss>
"""
