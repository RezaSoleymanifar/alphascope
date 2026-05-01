# AlphaScope roadmap

## Phase 0 — Skeleton (you are here)

- [x] Repo initialized
- [x] SQLite schema (papers, specs, results)
- [x] Source pollers: arXiv, SSRN, NBER, AlphaArchitect
- [x] Ingest pipeline + dedup
- [x] LLM triage scaffold (Anthropic Haiku)
- [x] Typer CLI: `init`, `poll`, `triage`, `stats`, `list`
- [x] Docs: README, architecture, methodology, roadmap

## Phase 1 — LLM extraction + first end-to-end

- [ ] PDF downloader + text extractor (pypdf)
- [ ] Sonnet-driven spec extractor → `specs` table populated
- [ ] Sonnet-driven code generator → `Spec.code` populated
- [ ] Sandbox executor (Docker, no network, time-limited)
- [ ] Smoke test: end-to-end on 5 known papers (Jegadeesh-Titman momentum, Fama-French value, AQR BAB, etc.)
- [ ] Human review queue for generated code

## Phase 2 — Backtest engine

- [ ] Price loader: yfinance MVP, EOD historical fallback
- [ ] Fundamentals loader: yfinance + grain integration
- [ ] FRED macro loader
- [ ] Universe loader (SP500 PIT membership approximation)
- [ ] IC report card
- [ ] Purged + embargoed CV
- [ ] DSR implementation
- [ ] Cost model (5bps + sqrt impact)
- [ ] Strategy stats (Sharpe, drawdown, Calmar, turnover)
- [ ] Regime analysis splits
- [ ] CPCV (Phase 2.5)

## Phase 3 — Web MVP (Streamlit)

- [ ] Streamlit dashboard
  - paper list with filters (source, status, tradable, sharpe>X)
  - per-paper detail page (spec, code, IC chart, equity curve, regime breakdown)
  - search by title/author/keyword
- [ ] Public deployment on Streamlit Cloud / Render
- [ ] Basic SEO (per-paper canonical URL, OG tags, sitemap)

## Phase 4 — Public launch (alphascope.io)

- [ ] Domain + DNS + Vercel/Railway deploy
- [ ] Next.js frontend replacing Streamlit
  - landing page with replicated paper count + top-Sharpe leaderboard
  - per-paper landing page (SEO-optimized)
  - search + filter
  - subscribe to RSS / weekly digest
- [ ] FastAPI backend for JSON API
- [ ] Postgres migration from SQLite
- [ ] Worker queue (Dramatiq)
- [ ] Monitoring (Sentry, Plausible analytics)

## Phase 5 — Community + crowdsourced

- [ ] User accounts (auth via GitHub OAuth)
- [ ] Submit-a-paper form (with anti-spam)
- [ ] Vote / discuss per paper
- [ ] User-submitted alternate implementations (with version diff)
- [ ] Comments + Q&A per paper
- [ ] Bounty for un-replicated high-impact papers

## Phase 6 — Live + alpha decay tracking

- [ ] Re-run all surviving signals weekly / monthly
- [ ] Track Sharpe / IC over time → alpha decay charts
- [ ] Email alerts when previously-shipped signal decays below threshold
- [ ] Compare published Sharpe (paper era) vs current Sharpe
- [ ] Public "factor zoo decay" page

## Phase 7 — Monetization (optional)

- [ ] Free tier: see all paper results
- [ ] Pro tier ($X/mo): API access, full backtest artifacts download, custom universe runs
- [ ] Enterprise: white-label methodology, custom data integrations, on-prem deployment for fund DD teams

## Phase 8 — Research lab (long-term)

- [ ] Native discovery (not just replication): generate alpha hypotheses via LLM, test them
- [ ] Ensemble: combine top-N signals into composite portfolio
- [ ] Live paper-trading for top signals (via Alpaca / IB)
- [ ] Research papers: AlphaScope itself publishes findings on factor zoo behavior

## Non-goals (intentionally not building)

- Custom QP solver (use OSQP/CVXPY)
- Proprietary data vendor (use commodity providers + caching)
- Live execution platform (focus is research, not trading)
- Mobile app (web is sufficient)
- Crypto-only (markets too immature for replication)
