"""Audit Sharadar Core US coverage against polled paper data requirements.

Sharadar Core US Fundamentals + SEP + ACTIONS + DAILY + TICKERS bundle:
- ~3000 US-listed tickers, 1999+
- ~150 PIT-timestamped fundamental line items per quarterly/annual filing
- Survivorship-bias-free (delisted firms retained with terminal records)
- Daily adjusted prices + volume + market cap + corporate actions
- NO intraday, NO international, NO options/futures, NO analyst data,
  NO Form 4, NO alt data, NO microstructure, NO derivatives.
"""
from __future__ import annotations

import json
import re
from collections import Counter

from alpha_archive.db import Session, Paper

COVERED = {
    "prices", "price", "adjusted_close", "adjusted_prices", "ohlc",
    "volume", "volumes", "adv", "dollar_volume", "turnover",
    "returns", "daily_returns", "monthly_returns",
    "market_cap", "marketcap", "shares_outstanding",
    "dividends", "dividend_yield", "splits", "corporate_actions",
    "delistings", "survivorship",
    "fundamentals", "earnings", "revenue", "income", "balance_sheet",
    "cashflow", "ebitda", "book_value", "debt", "assets", "equity",
    "roe", "roa", "gross_margin", "operating_margin", "free_cash_flow",
    "accruals", "asset_growth", "investment", "profitability",
    "leverage", "liquidity", "valuation", "pe", "pb", "ev_ebitda",
    "sector", "industry", "gics",
    "pit_fundamentals", "filing_date", "report_date",
}

PARTIAL = {
    "volatility", "realized_vol", "idiosyncratic_vol",  # derivable from prices
    "beta", "factor_betas", "fama_french",  # derivable
    "momentum", "reversal", "low_vol",  # derivable
    "size", "value", "quality", "investment_factor",  # derivable
    "intraday_price_structure",  # only EOD
    "high_low_range",  # only daily
}

NOT_COVERED = {
    "tick", "intraday", "minute_bars", "second_bars", "high_freq",
    "options", "options_chain", "implied_vol", "iv_surface",
    "futures", "derivatives", "swaps",
    "international", "non_us", "global", "europe", "asia", "emerging_markets",
    "analyst_forecasts", "ibes", "analyst_estimates", "consensus_estimates",
    "earnings_revisions", "recommendations",
    "insider_trades", "form_4", "13f", "13d",
    "news_sentiment", "tweets", "social_media", "web_traffic", "satellite",
    "alternative_data", "alt_data", "esg", "sustainability",
    "on_chain_metrics", "crypto", "btc", "eth", "blockchain",
    "fixed_income", "treasury_yields_detailed", "credit_spreads",
    "bid_ask", "order_flow", "microstructure", "limit_order_book",
    "10k_text", "8k_text", "filings_nlp", "earnings_calls", "transcripts",
    "patents", "supply_chain",
    "electricity_prices", "production_forecasts", "market_structure",
    "weather", "commodities_detailed",
    "segment_data", "geographic_segment",
    "credit_ratings",
}


def classify_token(t: str) -> str:
    t = t.lower().strip().replace("-", "_").replace(" ", "_")
    if t in COVERED:
        return "covered"
    if t in PARTIAL:
        return "partial"
    if t in NOT_COVERED:
        return "not_covered"
    # fallback: substring match
    for c in NOT_COVERED:
        if c in t or t in c:
            return "not_covered"
    for c in COVERED:
        if c in t or t in c:
            return "covered"
    for c in PARTIAL:
        if c in t or t in c:
            return "partial"
    return "unknown"


def score_paper(data_required: list[str]) -> tuple[str, list[tuple[str, str]]]:
    """Return verdict in {full, partial, blocked, unknown} + per-token classifications."""
    if not data_required:
        return "unknown", []
    cls = [(t, classify_token(t)) for t in data_required]
    classes = [c for _, c in cls]
    if any(c == "not_covered" for c in classes):
        return "blocked", cls
    if all(c == "covered" for c in classes):
        return "full", cls
    if any(c == "covered" or c == "partial" for c in classes):
        return "partial", cls
    return "unknown", cls


def parse_notes(p):
    n = p.triage_notes
    if isinstance(n, str):
        try: return json.loads(n)
        except: return {}
    return n or {}


def main() -> None:
    s = Session()
    papers = s.query(Paper).filter(Paper.triage_notes.isnot(None)).all()
    tradable = [p for p in papers if parse_notes(p).get("is_tradable")]
    print(f"== Sharadar coverage audit ==")
    print(f"triaged: {len(papers)} | tradable: {len(tradable)}")
    print()

    verdict_counts: Counter = Counter()
    per_paper: list[tuple[Paper, str, list]] = []

    for p in tradable:
        n = parse_notes(p)
        dr = n.get("data_required") or []
        if isinstance(dr, str):
            dr = [t.strip() for t in re.split(r"[,;]", dr) if t.strip()]
        verdict, cls = score_paper(dr)
        verdict_counts[verdict] += 1
        per_paper.append((p, verdict, cls))

    print("Coverage verdict rollup")
    print("-" * 40)
    for v in ("full", "partial", "blocked", "unknown"):
        c = verdict_counts.get(v, 0)
        pct = 100 * c / max(len(tradable), 1)
        print(f"  {v:>8}: {c:>3}  ({pct:>5.1f}%)")
    print()

    print("Per-paper detail")
    print("-" * 80)
    for p, v, cls in sorted(per_paper, key=lambda x: x[1]):
        title = (p.title or "")[:75]
        sym = {"full": "[FULL]", "partial": "[PART]", "blocked": "[BLOK]", "unknown": "[??? ]"}[v]
        print(f"{sym} #{p.id} | {title}")
        for tok, c in cls:
            mark = {"covered": "+", "partial": "~", "not_covered": "-", "unknown": "?"}[c]
            print(f"           {mark} {tok}  ({c})")
        print()


if __name__ == "__main__":
    main()
