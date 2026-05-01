"""Smoke tests: ingest works without LLM, db schema valid."""
from __future__ import annotations

import pytest


def test_db_initializes(tmp_path, monkeypatch):
    """Schema creates without error."""
    from alpha_archive import db
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.sqlite")
    db.ENGINE = db.create_engine(f"sqlite:///{tmp_path / 'test.sqlite'}", future=True)
    db.Session = db.sessionmaker(bind=db.ENGINE, autoflush=False, expire_on_commit=False)
    p = db.init_db()
    assert p.exists()


def test_arxiv_poller_smoke():
    """arXiv API actually returns parseable feed."""
    from alpha_archive.sources.arxiv import poll_arxiv
    rows = poll_arxiv(n=3)
    assert isinstance(rows, list)
    if rows:  # network may be down
        r = rows[0]
        assert r["source"] == "arxiv"
        assert r["external_id"]
        assert r["title"]
        assert r["landing_url"]


def test_alphaarchitect_poller_smoke():
    """AlphaArchitect RSS parses without error."""
    from alpha_archive.sources.alpha_architect import poll_alpha_architect
    rows = poll_alpha_architect(limit=3)
    assert isinstance(rows, list)


def test_nber_poller_smoke():
    """NBER RSS parses without error."""
    from alpha_archive.sources.nber import poll_nber
    rows = poll_nber(limit=3)
    assert isinstance(rows, list)
