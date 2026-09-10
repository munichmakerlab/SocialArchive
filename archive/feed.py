"""Minimal hand-written RSS 2.0 generator (no external feed library dependency)."""

from datetime import datetime
from xml.sax.saxutils import escape

from archive.models import Post

FEED_TITLE = "Munich Maker Lab -- Social Archive"
FEED_LINK = "https://posts.munichmakerlab.de/"
FEED_DESCRIPTION = "Archived posts from all MuMaLab social media accounts."


def _rfc822(dt: datetime) -> str:
    return dt.strftime("%a, %d %b %Y %H:%M:%S %z")


def build_feed_xml(posts: list[Post]) -> str:
    items = []
    for post in posts:
        primary_url = post.sources[0].url if post.sources else FEED_LINK
        enclosures = "".join(
            f'<enclosure url="{escape(m.url)}" type="{"video/mp4" if m.type == "video" else "image/jpeg"}"/>'
            for m in post.media
        )
        items.append(
            f"""  <item>
    <guid isPermaLink="false">{escape(post.id)}</guid>
    <link>{escape(primary_url)}</link>
    <pubDate>{_rfc822(post.published_at)}</pubDate>
    <description><![CDATA[{post.html}]]></description>
    {enclosures}
  </item>"""
        )

    items_xml = "\n".join(items)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>{escape(FEED_TITLE)}</title>
  <link>{escape(FEED_LINK)}</link>
  <description>{escape(FEED_DESCRIPTION)}</description>
{items_xml}
</channel>
</rss>
"""
