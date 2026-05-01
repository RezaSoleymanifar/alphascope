"""Ingest pipeline: poll all sources, dedupe, write to SQLite."""
from __future__ import annotations

from datetime import datetime
from typing import Callable

from sqlalchemy import select

from .db import Paper, Session, init_db
from .sources import poll_arxiv, poll_ssrn, poll_nber, poll_alpha_architect

SOURCES: dict[str, Callable] = {
    "arxiv": poll_arxiv,
    "ssrn": poll_ssrn,
    "nber": poll_nber,
    "alpha_architect": poll_alpha_architect,
}


def ingest(source: str = "all", limit: int | None = None) -> dict:
    """Poll source(s) and insert new papers. Idempotent (UNIQUE on source+external_id)."""
    init_db()

    targets = SOURCES.keys() if source == "all" else [source]
    summary = {}

    with Session() as s:
        for src in targets:
            try:
                rows = SOURCES[src](limit) if limit else SOURCES[src]()
            except TypeError:
                # source doesn't accept limit
                rows = SOURCES[src]()

            n_new = n_dup = 0
            for r in rows:
                existing = s.scalar(
                    select(Paper).where(
                        Paper.source == r["source"],
                        Paper.external_id == r["external_id"],
                    )
                )
                if existing:
                    n_dup += 1
                    continue
                s.add(Paper(**{
                    "source": r["source"],
                    "external_id": r["external_id"],
                    "title": r["title"],
                    "abstract": r.get("abstract"),
                    "authors": r.get("authors"),
                    "published_at": r.get("published_at"),
                    "pdf_url": r.get("pdf_url"),
                    "landing_url": r.get("landing_url"),
                    "categories": r.get("categories"),
                    "raw": r.get("raw"),
                }))
                n_new += 1
            s.commit()
            summary[src] = {"new": n_new, "duplicate": n_dup, "total_polled": len(rows)}

    return summary


if __name__ == "__main__":
    import json
    print(json.dumps(ingest(source="all"), indent=2))
