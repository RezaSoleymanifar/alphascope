"""Autonomous external-mention scraper.

Daily job that searches for AlphaScope replication mentions and external
critiques across:
  - Twitter/X (via API or scrape; STUB)
  - Reddit r/algotrading, r/quant (via PRAW or web scrape; STUB)
  - GitHub issues on the alphascope repo (via gh API; works today)
  - Substack / blog posts (via RSS aggregation; STUB)

Each mention becomes a CommunitySignal row in the DB. LLM classifies as:
  endorsement | critique | alternative | discussion

Verified critiques (after de-duplication + LLM agreement check) get auto-
promoted to community submissions for human voting.

This is a STUB skeleton in v0.1.0 — flesh out per source in Phase 5.
"""
from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass
class ExternalMention:
    source: str
    source_url: str
    raw_text: str
    paper_id_guess: int | None = None


def scrape_github_issues(repo: str = "RezaSoleymanifar/alphascope") -> list[ExternalMention]:
    """Fetch open issues on the alphascope repo. Working today via `gh` CLI."""
    import subprocess
    try:
        out = subprocess.run(
            ["gh", "issue", "list", "--repo", repo, "--state", "all", "--json",
             "number,title,body,url,createdAt", "--limit", "50"],
            capture_output=True, text=True, timeout=30,
        )
    except Exception as e:
        return []
    if out.returncode != 0:
        return []
    try:
        items = json.loads(out.stdout)
    except json.JSONDecodeError:
        return []
    return [
        ExternalMention(
            source="github_issue",
            source_url=it["url"],
            raw_text=f"{it['title']}\n\n{it.get('body', '')}",
        )
        for it in items
    ]


def scrape_twitter(query: str) -> list[ExternalMention]:
    """STUB: requires Twitter API v2 access (paid tier)."""
    return []


def scrape_reddit(subreddits: list[str], query: str) -> list[ExternalMention]:
    """STUB: requires PRAW + Reddit OAuth."""
    return []


def scrape_substack(feed_urls: list[str]) -> list[ExternalMention]:
    """STUB: parse Substack RSS for paper-title mentions."""
    return []


CLASSIFY_PROMPT = """You are classifying an external mention of an AlphaScope paper replication.

The mention text is:
---
{text}
---

Classify the mention as ONE of:
  endorsement   (positive, agrees with AlphaScope's verdict)
  critique      (challenges methodology, data, or verdict)
  alternative   (proposes a different implementation)
  discussion    (neutral discussion, no actionable claim)
  unrelated     (does not actually reference an AlphaScope replication)

Output JSON: {{"signal_type": ..., "extracted_claim": "1-sentence", "actionable": true|false}}
"""


def classify_mention(mention: ExternalMention) -> dict:
    from ..llm import get_provider
    provider = get_provider()
    return provider.complete_json(
        CLASSIFY_PROMPT.format(text=mention.raw_text[:3000]),
        model="haiku",
        max_tokens=200,
    )


def run_daily_scrape() -> dict:
    """Top-level scrape job. Returns summary."""
    mentions = scrape_github_issues()
    # + scrape_twitter(...), scrape_reddit(...), scrape_substack(...) when configured
    return {
        "github_issues": len(mentions),
        "twitter": 0,
        "reddit": 0,
        "substack": 0,
        "note": "twitter/reddit/substack are stubs in v0.1.0",
    }
