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
git clone https://github.com/<you>/alpha-archive
cd alpha-archive
uv sync                         # Python env
uv run alpha-archive poll arxiv    # fetch new papers
uv run alpha-archive triage        # LLM triage queue
uv run alpha-archive eval <paper-id>
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
- **Phase 0**: Repo skeleton, schema, source pollers (you are here)
- **Phase 1**: LLM triage + spec extraction working on arXiv
- **Phase 2**: Backtest engine producing IC reports
- **Phase 3**: Web UI MVP (Streamlit)
- **Phase 4**: Public launch on alpha-archive.io
- **Phase 5**: Crowdsourced submissions + community

## Why this could become popular

- **SEO win**: each replicated paper = a landing page with original keywords + Sharpe + chart
- **Quant Twitter**: practitioners constantly debate factor zoo; Alpha Archive provides verdict-in-a-link
- **Educational**: students + retail quants can learn what works
- **Fund DD value**: hedge fund LPs use it to vet manager pitches ("did this actually work post-publication?")
- **Content engine**: weekly newsletter "5 papers replicated this week"
- **Recruiter signal**: every result is reproducible code → portfolio piece for QR jobs

## Status

**Phase 0** — repo scaffolding. Not production. Not financial advice. Use at your own risk.

## License

MIT (planned). Methodology + extracted code is open. Original papers belong to their authors.

## Author

Reza Soleymanifar · PhD UIUC · ML Engineer · [profile](https://github.com/<you>)
