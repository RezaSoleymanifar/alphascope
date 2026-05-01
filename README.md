# Alpha Archive

> **Every quantitative finance paper, replicated. Open. Verified.**

Alpha Archive is an automated signal-extraction engine. It ingests academic papers from arXiv / SSRN / NBER, uses LLMs to extract the trading signal specification, runs each through a standardized backtest pipeline, and publishes the results.

## Why this exists

- **400+ "factors"** have been published in academic finance journals. Most decay or never worked. Nobody knows which to trust.
- **Replication is manual today** — sites like AlphaArchitect do it by hand, ~50 papers/year.
- **Quantpedia charges $300/yr** for static curated database with no live re-runs.
- **Nothing exists** that's: (1) automated, (2) free, (3) live-updating, (4) standardized methodology, (5) crowdsourced.

LLMs can now read papers, extract signal specifications, and write the implementation code. Alpha Archive is the productized version of that loop.

## What it does

```
arXiv / SSRN / NBER feed   →   LLM triage (is this tradable?)
                           →   LLM extracts spec (formula, data, horizon, claimed Sharpe)
                           →   Auto-generates feature.py implementation
                           →   Runs purged-CV backtest with DSR correction
                           →   Publishes result on alpha-archive.io/papers/{id}
                           →   Tracks alpha decay over time
```

Each paper gets a public landing page with:
- Original paper link + author
- LLM-extracted signal specification
- Generated Python implementation (open, auditable)
- Backtest: IC report card, DSR-adjusted Sharpe, decay curve, regime analysis
- Replication score: gap between paper claims and live result
- Comments / community discussion

## Relationship to Hou-Xue-Zhang 2018 ("Replicating Anomalies")

HXZ 2018 is the gold-standard one-shot replication study: 452 published anomalies, all run through one consistent pipeline, with a multiple-testing-corrected significance bar (t > 2.78). Roughly 64% of the published "discoveries" failed to replicate. It permanently moved the goalposts for credible factor research and is the closest existing analogue to what Alpha Archive aims to be.

Alpha Archive is the **autonomous, perpetually-running version of HXZ**:

| | HXZ 2018 | Alpha Archive |
|---|---|---|
| Scope | 452 finished papers, one-shot | Every new paper as it drops, continuous |
| Pipeline | Manual, single team, single dataset | Automated LLM extraction + standardized backtest |
| Significance bar | Single threshold across the 452 | Cumulative DSR adjustment across all papers ever tested |
| Result lifecycle | Frozen at publication | Live re-runs track alpha decay over time |
| Code / data | Closed source-of-truth | Open code, open results, crowdsourced verification |

The methodology HXZ established — point-in-time data, survivorship-free universe, purged CV, multiple-testing correction — is the methodology spec here. See [docs/methodology.md](./docs/methodology.md). After HXZ, no credible factor paper can skip these checks; Alpha Archive enforces them automatically and at scale.

## Differentiators

| | AlphaArchitect | Quantpedia | Alpha Archive |
|---|---|---|---|
| Cost | Free blog | $300/yr | Free + open |
| Coverage | ~50 papers/yr (manual) | 700+ static | 1000s/yr automated |
| Reproducible code | Sometimes | Some | Always (auto-gen + open) |
| Live re-runs | No | No | Continuously updated |
| Methodology standardized | No | Partial | Yes (purged CV + DSR everywhere) |
| Crowdsourced | No | No | Yes (challenges, alts, votes) |
| Tracks alpha decay | No | No | Yes (live re-run cadence) |

## Vision: Central intelligence for quant finance

Alpha Archive combines three loops into one knowledge base:

1. **Automated replication** — LLM reads paper, extracts spec, writes code, runs backtest
2. **Meta-learning critique** — internal critic agent judges every result; actor self-improves; learn improves the critic
3. **Crowdsourced verification** — community submits challenges, alternatives, annotations; Twitter-Community-Notes-style bipartisan agreement gates merges

The result: one canonical, continuously-updated, executable, community-verified page per quant finance paper.

Like Wikipedia for trading signals, with executable code + live backtests + bipartisan verification.

## Quick start (developer)

```bash
git clone https://github.com/RezaSoleymanifar/alpha-archive
cd alpha-archive
uv sync                                                # Python env
uv run alpha-archive init                              # SQLite schema
uv run alpha-archive install-fixtures                  # 326 ground-truth fixtures from OpenAP
uv run alpha-archive poll arxiv                        # fetch new papers
uv run alpha-archive triage --limit 20                 # LLM triage (free via Claude Code CLI)
uv run alpha-archive replicate <paper_id> <pdf_url>    # end-to-end paper → verdict
```

## Architecture

```
[Paper sources]               [LLM layer]              [Backtest engine]        [Web UI]
arXiv RSS / API     ─┐        ┌─ Triage              ┌─ Data: yfinance,        ┌─ Next.js
SSRN scraper        ─┤  →     ├─ Spec extractor  →   │  EOD, FRED, grain  →   ├─ Per-paper page
NBER RSS            ─┤        └─ Code generator     ├─ IC report card        ├─ Search / filter
AlphaArchitect RSS  ─┘                              ├─ Purged CV + DSR       ├─ Submit paper
Manual submission   ─┘                              ├─ Decay analysis        ├─ Discussion
                                                    └─ Regime test           └─ API
```

See [docs/architecture.md](./docs/architecture.md) for full layout.

## Data layer

Methodology (purged CV, DSR, replication scores) is independent of any specific data vendor; the same pipeline runs on whatever price + fundamentals panel you point it at. Practical retail-tier stack:

| Source | Cost | Role |
|---|---|---|
| **Sharadar Core US Fundamentals** (Nasdaq Data Link) | ~$200/mo | Point-in-time fundamentals + adjusted prices + delisting actions, ~3000 US tickers since 1999. The single biggest unlock — solves survivorship-bias and lookahead-bias blockers in one subscription. |
| **Ken French data library** | free | Fama-French + Carhart benchmark factor return series for alpha computation |
| **HXZ q-factors** (authors' site) | free | q-factor return series for HXZ-style alpha decomposition |
| **FRED** | free | Macro (rates, inflation, VIX, credit spreads) for regime-conditional analysis |
| **EODHD** | $79/mo | International universe + intraday — complementary, not core |

Without point-in-time fundamentals + a survivorship-free universe, all replications are biased upward. Until Sharadar (or equivalent) is wired in, the pipeline is restricted to **price-and-ADV-only anomalies** — roughly 25 of HXZ's 452, including 12-1 momentum, idiosyncratic volatility, MAX, betting-against-beta proxies, and long-term reversal. That is a credible Phase-1 scope.

WRDS-tier data (CRSP, Compustat, I/B/E/S, TAQ, OptionMetrics) is institutional-only and unlocks the remaining ~25% of HXZ that depends on full Compustat-depth line items, analyst forecasts, or microstructure. Out of scope for retail.

## Companion repo: portfolio-management

Alpha Archive answers "does this signal work?" — it produces a catalog of validated signals with replication scores and decay curves. The companion repo [`portfolio-management`](../portfolio-management) answers the next question: "given working signals, how do I build a portfolio from them?"

```
alpha-archive (this repo)              portfolio-management
──────────────────────────             ──────────────────────────
INPUT:  papers (arxiv/SSRN/NBER)       INPUT:  validated signals
OUTPUT: validated signals,             OUTPUT: weight vector w
        replication scores,                    (which stocks, how much $)
        decay curves
JOB:    Does this signal work?         JOB:    Given working signals,
                                               build a portfolio.
```

The optimizer in `portfolio-management` (long-only retail convex QP with sector-balance constraints, six factor presets, plus an HRP alternative) consumes the signals validated here. Together they form an end-to-end pipeline: paper → signal validation → portfolio allocation.

## Methodology

Every paper goes through the same pipeline. No cherry-picking, no parameter tuning per paper. Documented in [docs/methodology.md](./docs/methodology.md).

Key principles:
- **Purged k-fold CV** with embargo (Lopez de Prado 2018)
- **Deflated Sharpe Ratio** (Bailey + Lopez de Prado 2014) corrected for ALL papers tested across the platform
- **Pre-registered OOS window**: last 2 years held out from training
- **Standardized cost model**: 5bps round-trip + impact = σ × √(Q/ADV)
- **Replication score**: published Sharpe vs our Sharpe (after corrections)

## Roadmap

See [docs/roadmap.md](./docs/roadmap.md). Phased:
- **Phase 0** ✅ Repo skeleton, SQLite schema, six source pollers (arXiv, SSRN, NBER, AlphaArchitect, AQR, Two Sigma), Typer CLI
- **Phase 0.5** ✅ **Fixture calibration** — 326 ground-truth fixtures bootstrapped from Open Source Asset Pricing (Chen+Zimmermann), plus hand-coded canonical anomalies (12-1 momentum). Meta-loop now F1-meaningful.
- **Phase 1** ✅ LLM triage + spec extraction + code generation, end-to-end demo on real arXiv paper (VP-MACD). Pluggable provider abstraction: `claude_code` (free via Max plan) | `anthropic` (API key) | `offline` (no LLM)
- **Phase 2** 🟡 Backtest engine: purged CV, DSR, IC report, asymmetric verdict assignment shipped. Cost model + regime splits in progress.
- **Phase 2.5** 🟡 **Meta-learning loop** — actor/critic/learn governance scaffolded under `meta/`; community layer (Tier-1 GitHub-issue-based crowdsourcing, Community-Notes-style bipartisan agreement) scaffolded under `alpha_archive/community/`
- **Phase 3** ⏳ Web UI MVP (Streamlit)
- **Phase 4** ⏳ Public launch on alpha-archive.io
- **Phase 5** ⏳ Crowdsourced submissions + bipartisan verification at scale

## Why this could become popular

- **SEO win**: each replicated paper = a landing page with original keywords + Sharpe + chart
- **Quant Twitter**: practitioners constantly debate factor zoo; Alpha Archive provides verdict-in-a-link
- **Educational**: students + retail quants can learn what works
- **Fund DD value**: hedge fund LPs use it to vet manager pitches ("did this actually work post-publication?")
- **Content engine**: weekly newsletter "5 papers replicated this week"
- **Recruiter signal**: every result is reproducible code → portfolio piece for QR jobs

## Status

**Phase 2** — pipeline operational end-to-end on real papers (proof-of-life: see [docs/demo_run.md](./docs/demo_run.md)). Meta-learning + community layers scaffolded. Pre-Streamlit. Not production. Not financial advice. Use at your own risk.

## License

MIT (planned). Methodology + extracted code is open. Original papers belong to their authors.

## Author

Reza Soleymanifar · PhD UIUC · ML Engineer · [profile](https://github.com/RezaSoleymanifar)
