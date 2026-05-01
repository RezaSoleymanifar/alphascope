"""SSRN scraper. SSRN doesn't offer a clean API; we scrape the top-papers
listing for the FEN (Financial Economics Network) finance ejournal.

This module is a stub — fill in based on current SSRN HTML structure.
SSRN periodically changes its layout; treat scraping as best-effort.
"""
from __future__ import annotations

import re
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

# Top SSRN ejournals for quant finance
SSRN_TOP_FEN = "https://papers.ssrn.com/sol3/JELJOUR_Results.cfm?form_name=journalbrowse&journal_id=2755100"
SSRN_DOWNLOAD = "https://papers.ssrn.com/sol3/papers.cfm?abstract_id={id}"


def poll_ssrn(limit: int = 50) -> list[dict]:
    """Poll SSRN top-downloads page (best-effort scrape).
    Returns list of paper dicts in standardized format.

    NOTE: SSRN aggressively rate-limits and changes HTML layout.
    Production deployment should use a proper SSRN data provider or
    consume their RSS feeds where available.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; AlphaArchive/0.1; +https://alpha-archive.io)"
        )
    }
    try:
        r = httpx.get(SSRN_TOP_FEN, headers=headers, timeout=20, follow_redirects=True)
        r.raise_for_status()
    except Exception as e:
        print(f"[ssrn] fetch failed: {e}")
        return []

    soup = BeautifulSoup(r.text, "lxml")
    out = []
    for a in soup.select("a[href*='papers.cfm?abstract_id=']"):
        href = a.get("href", "")
        m = re.search(r"abstract_id=(\d+)", href)
        if not m:
            continue
        aid = m.group(1)
        title = a.get_text(strip=True)
        if not title or len(title) < 10:
            continue
        out.append({
            "source": "ssrn",
            "external_id": aid,
            "title": title,
            "abstract": None,  # requires per-paper fetch; leave for triage stage
            "authors": None,
            "published_at": None,
            "pdf_url": None,
            "landing_url": SSRN_DOWNLOAD.format(id=aid),
            "categories": "FEN",
            "raw": {"href": href},
        })
        if len(out) >= limit:
            break
    return out


if __name__ == "__main__":
    rows = poll_ssrn(limit=10)
    for r in rows:
        print(f"- [{r['external_id']}] {r['title'][:80]}")
    print(f"\ntotal: {len(rows)}")
