"""Merge cross-platform duplicate posts (the same content cross-posted to
multiple platforms) into one canonical Post with multiple `sources`.

Calibrated against the real archive data: an automated tool cross-posts to
Mastodon and Bluesky within the same instant, so real duplicates land well
within a generous time window and score far above unrelated posts on a
normalized, token-set text similarity. See the plan/commit message for the
actual scores this was tuned against. Known limitation: a post reworded
very differently per platform (low text similarity) won't be caught --
that needs image/semantic matching, deliberately not implemented here.
"""

import itertools
import re
from datetime import timedelta

from rapidfuzz import fuzz

from archive.models import Post

PLATFORM_PRIORITY = ["mastodon", "bluesky", "tumblr", "instagram", "twitter"]
TIME_WINDOW = timedelta(hours=6)
SIMILARITY_THRESHOLD = 80  # rapidfuzz token_set_ratio, 0-100

_URL_RE = re.compile(r"https?://\S+")
_HASHTAG_RE = re.compile(r"#\w+")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9\s]")
_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_text(text: str) -> str:
    text = text.lower()
    text = _URL_RE.sub("", text)
    text = _HASHTAG_RE.sub("", text)
    text = _NON_ALNUM_RE.sub(" ", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def _platform_of(post: Post) -> str:
    return post.sources[0].platform


def _platform_rank(platform: str) -> int:
    return PLATFORM_PRIORITY.index(platform) if platform in PLATFORM_PRIORITY else len(PLATFORM_PRIORITY)


def _find_candidate_pairs(posts: list[Post]) -> list[tuple[float, int, int]]:
    normalized = [_normalize_text(p.text) for p in posts]
    candidates = []
    for i, j in itertools.combinations(range(len(posts)), 2):
        a, b = posts[i], posts[j]
        if _platform_of(a) == _platform_of(b):
            continue
        if not normalized[i] or not normalized[j]:
            continue
        if abs((a.published_at - b.published_at)) > TIME_WINDOW:
            continue
        score = fuzz.token_set_ratio(normalized[i], normalized[j])
        if score >= SIMILARITY_THRESHOLD:
            candidates.append((score, i, j))
    return candidates


def _cluster(posts: list[Post], candidates: list[tuple[float, int, int]]) -> list[list[int]]:
    clusters = [[i] for i in range(len(posts))]
    index_of = list(range(len(posts)))  # index_of[i] = which cluster (by position in `clusters`) post i is in

    # stable order: highest score first, tie-break on post id for reproducibility
    candidates = sorted(candidates, key=lambda c: (-c[0], posts[c[1]].id, posts[c[2]].id))

    for _, i, j in candidates:
        ci, cj = index_of[i], index_of[j]
        if ci == cj:
            continue
        cluster_i, cluster_j = clusters[ci], clusters[cj]
        platforms_i = {_platform_of(posts[k]) for k in cluster_i}
        platforms_j = {_platform_of(posts[k]) for k in cluster_j}
        if platforms_i & platforms_j:
            continue  # would put two posts from the same platform in one cluster

        merged = cluster_i + cluster_j
        clusters[ci] = merged
        clusters[cj] = []
        for k in merged:
            index_of[k] = ci

    return [c for c in clusters if c]


def _merge_cluster(posts: list[Post], indices: list[int]) -> Post:
    members = sorted((posts[i] for i in indices), key=lambda p: _platform_rank(_platform_of(p)))
    primary = members[0]

    tags: list[str] = []
    for member in members:
        for tag in member.tags:
            if tag not in tags:
                tags.append(tag)

    sources = [source for member in members for source in member.sources]

    return primary.model_copy(
        update={
            "sources": sources,
            "tags": tags,
            "published_at": min(m.published_at for m in members),
            "updated_at": max(m.updated_at for m in members),
        }
    )


def deduplicate(posts: list[Post]) -> list[Post]:
    if len(posts) < 2:
        return posts

    candidates = _find_candidate_pairs(posts)
    clusters = _cluster(posts, candidates)
    return [_merge_cluster(posts, indices) for indices in clusters]
