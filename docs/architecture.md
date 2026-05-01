# Alpha Archive architecture

## Overview

Alpha Archive is a 5-layer pipeline:

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: SOURCES                                            │
│  arXiv RSS · SSRN scraper · NBER RSS · AlphaArchitect RSS   │
│  · manual submission                                         │
└────────────────────┬────────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: INGEST                                             │
│  Dedupe by (source, external_id) → SQLite `papers` table     │
└────────────────────┬────────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: LLM TRIAGE + EXTRACTION                            │
│  Haiku triage abstract → Sonnet extracts spec + writes code  │
│  → SQLite `specs` table                                      │
└────────────────────┬────────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: BACKTEST ENGINE                                    │
│  Loads price/fundamentals data → runs feature code →         │
│  IC report card → DSR-corrected Sharpe → SQLite `results`    │
└────────────────────┬────────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 5: WEB API + UI                                       │
│  FastAPI REST endpoints + Next.js (or Streamlit MVP)         │
│  Public per-paper landing pages                              │
└─────────────────────────────────────────────────────────────┘
```

## Data flow

1. **Cron** (or manual) triggers `alpha-archive poll <source>`.
2. Source poller returns standardized paper dicts.
3. Ingest dedupes against existing `papers` table; new rows get `triage_status=pending`.
4. **Triage worker** picks pending papers, calls Haiku with abstract → updates `triage_status` + `triage_score`.
5. **Extract worker** picks `tradable` papers, downloads PDF, calls Sonnet to extract spec + write code → inserts `specs` row.
6. **Backtest worker** picks new `specs`, executes feature code on local data, computes IC report + DSR + replication score → inserts `results` row.
7. **API** serves results to frontend; per-paper landing page renders.

## Storage

- **SQLite** for metadata (papers, specs, results) — sufficient until 100K+ papers
- **Parquet** for backtest artifacts (IC time series, equity curves, plots) — under `data/parquet/`
- **PDFs** cached under `data/papers/{paper_id}.pdf`
- Migration to **Postgres** when multi-tenant or write-heavy

## Compute

- MVP: single machine, sequential workers
- Phase 3+: Celery / Dramatiq queue, multiple workers
- Phase 5+: distributed backtest grid (Ray) for parameter sweeps

## Data sources for backtests

- **Prices**: yfinance (free, MVP) → EOD Historical Data ($20/mo) → Polygon ($99/mo)
- **Fundamentals**: yfinance + EOD → grain repo's `eodhd-fundamentals-cache.json`
- **Macro**: FRED (free) via `fredapi`
- **Alt data**: hooks for Form 4 insider trades, options activity, news sentiment

## LLM usage

- **Triage**: Haiku, ~200 tokens in / 100 tokens out per paper. Cost ~$0.001/paper.
- **Spec extraction**: Sonnet, ~5K tokens in (PDF text) / 2K tokens out. Cost ~$0.015/paper.
- **Code generation**: Sonnet, ~3K tokens in (spec) / 1K tokens out. Cost ~$0.010/paper.
- **Total per paper**: ~$0.026.
- **80K papers/yr**: ~$2,000/yr in LLM cost. Tractable.

## Web stack

- **Frontend**: Next.js 14+ (App Router) + Tailwind + Recharts/visx
- **Backend**: FastAPI for JSON API; static page generation for SEO
- **Hosting**:
  - API: Fly.io / Railway / Render
  - Frontend: Vercel
  - Database: Supabase or PlanetScale (Postgres) when migrating off SQLite
  - Workers: Modal or Railway

## Scaling milestones

| Stage | Papers | DB | Compute | Hosting cost/mo |
|---|---|---|---|---|
| MVP | <1K | SQLite | Single laptop | $0 |
| Public launch | 1K-10K | SQLite | Single VM | $20 |
| Growth | 10K-100K | Postgres | Multi-worker | $200 |
| Scale | 100K+ | Postgres + S3 parquet | Distributed | $1K-5K |

## Security / abuse

- Rate-limit API (per IP)
- Auth required for: paper submission, comments
- LLM-generated code runs in sandbox (Docker, no network, ephemeral filesystem)
- All extracted code is human-reviewable before backtest execution (configurable gate)

## Observability

- Structured logging (loguru → JSON)
- Per-paper run timeline (ingest → triage → extract → backtest → publish)
- Public dashboard: papers/day, triage hit rate, replication success rate
