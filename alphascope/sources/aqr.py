"""AQR Insights RSS poller. Real practitioner research from Asness/Frazzini/Pedersen team.
"""
from __future__ import annotations

from datetime import datetime

import feedparser

AQR_RSS_CANDIDATES = [
    "https://www.aqr.com/RssFeeds/research-insights",
    "https://www.aqr.com/Insights/Research/rss",
]


def poll_aqr(limit: int = 50) -> list[dict]:
    out = []
    for url in AQR_RSS_CANDIDATES:
        feed = feedparser.parse(url)
        if not feed.entries:
            continue
        for entry in feed.entries[:limit]:
            out.append({
                "source": "aqr",
                "external_id": _slug(entry.link),
                "title": (entry.title or "").strip(),
                "abstract": (getattr(entry, "summary", "") or "").strip(),
                "authors": getattr(entry, "author", "AQR Research"),
                "published_at": _parse_dt(getattr(entry, "published", None)),
                "pdf_url": None,
                "landing_url": entry.link,
                "categories": "aqr",
                "raw": {},
            })
        if out:
            break
    return out


def _slug(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1]


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


if __name__ == "__main__":
    rows = poll_aqr(limit=10)
    for r in rows:
        print(f"- [{r['external_id']}] {r['title'][:80]}")
    print(f"\ntotal: {len(rows)}")
