"""arXiv q-fin RSS poller.
arXiv categories of interest:
- q-fin.PM (Portfolio Management)
- q-fin.TR (Trading and Market Microstructure)
- q-fin.ST (Statistical Finance)
- q-fin.CP (Computational Finance)
- q-fin.RM (Risk Management)
- q-fin.GN (General Finance)
- q-fin.MF (Mathematical Finance)
- q-fin.PR (Pricing of Securities)
- q-fin.EC (Economics)
"""
from __future__ import annotations

from datetime import datetime
from typing import Iterable

import feedparser

ARXIV_CATEGORIES = [
    "q-fin.PM", "q-fin.TR", "q-fin.ST", "q-fin.CP",
    "q-fin.RM", "q-fin.GN", "q-fin.MF", "q-fin.PR",
]

ARXIV_API_TEMPLATE = (
    "http://export.arxiv.org/api/query?"
    "search_query={cats}&start=0&max_results={n}&sortBy=submittedDate&sortOrder=descending"
)


def _to_record(entry) -> dict:
    aid = entry.id.split("/abs/")[-1]
    return {
        "source": "arxiv",
        "external_id": aid,
        "title": (entry.title or "").strip().replace("\n", " "),
        "abstract": (getattr(entry, "summary", "") or "").strip().replace("\n", " "),
        "authors": ", ".join(a.name for a in getattr(entry, "authors", [])),
        "published_at": _parse_dt(getattr(entry, "published", None)),
        "pdf_url": next(
            (l.href for l in getattr(entry, "links", []) if getattr(l, "type", "") == "application/pdf"),
            f"https://arxiv.org/pdf/{aid}.pdf",
        ),
        "landing_url": entry.link,
        "categories": ", ".join(t.term for t in getattr(entry, "tags", [])),
        "raw": {"id": entry.id},
    }


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def poll_arxiv(categories: Iterable[str] = ARXIV_CATEGORIES, n: int = 100) -> list[dict]:
    """Poll arXiv API for recent papers in the given categories."""
    cats = "+OR+".join(f"cat:{c}" for c in categories)
    url = ARXIV_API_TEMPLATE.format(cats=cats, n=n)
    feed = feedparser.parse(url)
    return [_to_record(e) for e in feed.entries]


if __name__ == "__main__":
    import json
    rows = poll_arxiv(n=5)
    for r in rows:
        print(f"- [{r['external_id']}] {r['title'][:80]}")
    print(f"\ntotal: {len(rows)}")
