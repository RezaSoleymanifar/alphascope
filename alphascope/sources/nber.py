"""NBER (National Bureau of Economic Research) working papers RSS poller.
Free abstracts, paid PDFs ($5/each or $90/yr unlimited subscription).
Most NBER finance papers also appear on SSRN.
"""
from __future__ import annotations

from datetime import datetime

import feedparser

NBER_RSS = "https://www.nber.org/papers/rss"


def poll_nber(limit: int = 50) -> list[dict]:
    feed = feedparser.parse(NBER_RSS)
    out = []
    for entry in feed.entries[:limit]:
        wp = entry.link.rsplit("/", 1)[-1]  # e.g. w12345
        out.append({
            "source": "nber",
            "external_id": wp,
            "title": (entry.title or "").strip(),
            "abstract": (getattr(entry, "summary", "") or "").strip(),
            "authors": getattr(entry, "author", None),
            "published_at": _parse_dt(getattr(entry, "published", None)),
            "pdf_url": f"https://www.nber.org/papers/{wp}.pdf",
            "landing_url": entry.link,
            "categories": "NBER",
            "raw": {},
        })
    return out


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


if __name__ == "__main__":
    rows = poll_nber(limit=10)
    for r in rows:
        print(f"- [{r['external_id']}] {r['title'][:80]}")
    print(f"\ntotal: {len(rows)}")
