"""LLM triage: read each pending paper's abstract, decide if it describes a
tradable signal. Updates papers.triage_status and papers.triage_score.

Uses Anthropic SDK with Claude Haiku (cheap + fast for scan workload).
Set ANTHROPIC_API_KEY env var.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Optional

from sqlalchemy import select

from .db import Paper, Session


TRIAGE_MODEL = "claude-haiku-4-5-20251001"

TRIAGE_PROMPT = """You are a quantitative finance research analyst. You read paper abstracts and decide if the paper describes a tradable trading signal that could be backtested.

A "tradable signal" means:
- Predicts future asset returns (cross-sectional or time-series)
- Defines a signal that can be computed from available data (prices, fundamentals, alternative data)
- Has a defined investment universe and horizon

NOT tradable:
- Pure theoretical asset pricing without empirical signal
- Macro regime forecasting without portfolio rule
- Survey or literature review
- Risk management methodology without alpha component
- Pricing of exotic derivatives without hedging signal

Given this paper:

TITLE: {title}
ABSTRACT: {abstract}

Output strict JSON:
{{
  "is_tradable": true | false,
  "confidence": 0.0 to 1.0,
  "signal_type": "cross_sectional_equity" | "time_series" | "macro" | "options_vol" | "credit" | "other" | null,
  "data_required": ["prices", "fundamentals", "macro", "alt", ...],
  "horizon_days": int or null,
  "claimed_sharpe": number or null,
  "notes": "1-sentence summary"
}}
"""


def _client():
    """Lazy-init Anthropic client. Raises if key missing."""
    try:
        from anthropic import Anthropic
    except ImportError as e:
        raise RuntimeError("install with: uv add anthropic") from e
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY env var not set")
    return Anthropic(api_key=key)


def triage_one(paper: Paper, client=None) -> dict:
    """Triage a single paper. Returns the parsed JSON dict."""
    if client is None:
        client = _client()
    prompt = TRIAGE_PROMPT.format(
        title=paper.title or "(no title)",
        abstract=(paper.abstract or "(no abstract)")[:4000],
    )
    msg = client.messages.create(
        model=TRIAGE_MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text.strip()
    # strip code fences if model wrapped in ```json ... ```
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip().rstrip("`").strip()
    return json.loads(text)


def triage_pending(limit: int = 50, dry_run: bool = False) -> dict:
    """Triage up to `limit` papers with status='pending'."""
    client = _client() if not dry_run else None
    n_tradable = n_not = n_err = 0
    with Session() as s:
        rows = list(s.scalars(
            select(Paper)
            .where(Paper.triage_status == "pending")
            .order_by(Paper.published_at.desc().nulls_last())
            .limit(limit)
        ))
        for p in rows:
            if dry_run:
                print(f"[dry] would triage: {p.title[:80]}")
                continue
            try:
                result = triage_one(p, client)
                p.triage_status = "tradable" if result.get("is_tradable") else "not_tradable"
                p.triage_score = float(result.get("confidence") or 0)
                p.triage_notes = json.dumps(result)
                p.triaged_at = datetime.utcnow()
                if result.get("is_tradable"):
                    n_tradable += 1
                else:
                    n_not += 1
            except Exception as e:
                p.triage_status = "error"
                p.triage_notes = str(e)[:500]
                p.triaged_at = datetime.utcnow()
                n_err += 1
            s.commit()
    return {
        "tradable": n_tradable,
        "not_tradable": n_not,
        "errors": n_err,
        "scanned": len(rows),
    }


if __name__ == "__main__":
    import json as _json
    print(_json.dumps(triage_pending(limit=10, dry_run=True), indent=2))
