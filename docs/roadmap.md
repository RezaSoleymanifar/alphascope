# Alpha Archive roadmap

## Phase 0 — Skeleton ✅ shipped

- [x] Repo initialized
- [x] SQLite schema (papers, specs, results)
- [x] Source pollers: arXiv, SSRN, NBER, AlphaArchitect, AQR, Two Sigma (curated-first hierarchy)
- [x] Ingest pipeline + dedup
- [x] LLM triage scaffold (Claude Haiku)
- [x] Typer CLI: `init`, `poll`, `triage`, `stats`, `list`, `replicate`, `install-fixtures`, `evaluate`, `llm-info`
- [x] Docs: README, architecture, methodology, roadmap, demo_run, go-to-market, meta_learning

## Phase 0.5 — Fixture calibration ✅ shipped

- [x] OpenAP CrossSection bootstrap loader → 326 ground-truth fixtures with literature labels (165 ship / 47 iterate / 114 kill)
- [x] Hand-coded canonical anomalies (Jegadeesh-Titman 1993 momentum)
- [x] Adversarial random fixtures for FP-rate calibration
- [x] Fixture set total: 332 (was 6 pre-bootstrap) → meta-loop F1 now statistically meaningful

## Phase 1 — LLM extraction + first end-to-end ✅ shipped

- [x] PDF downloader + text extractor (pypdf, 30 pages)
- [x] Sonnet-driven spec extractor with self-consistency check (run 2× different temps, agreement ≥ 0.85 gate)
- [x] Sonnet-driven code generator → `Spec.code` populated
- [x] Sandbox executor (restricted-builtins exec, no network, deterministic, time-limited)
- [x] AST-level validation gates: signature, imports, no-lookahead, no-banned-tokens, deterministic
- [x] End-to-end smoke test on real arXiv paper (VP-MACD, see [docs/demo_run.md](./demo_run.md))
- [x] Pluggable LLM provider abstraction: `claude_code` (free via Max plan) | `anthropic` (API key) | `offline`

## Phase 2 — Backtest engine 🟡 in progress

- [x] Price loader: grain parquet primary, yfinance fallback
- [x] Universe loader (SP500 from grain snapshot — PIT approximation)
- [x] IC report card (mean, std, ICIR, t-stat)
- [x] Purged + embargoed CV
- [x] DSR implementation (Bailey + Lopez de Prado 2014)
- [x] Strategy stats (Sharpe, drawdown, turnover)
- [x] Asymmetric verdict assignment (ship / iterate / kill — bias toward iterate)
- [ ] Cost model (5bps + sqrt market impact) — basic 5bps in place; impact term pending
- [ ] Fundamentals loader (Sharadar Core US — gated on $200/mo subscription decision)
- [ ] FRED macro loader
- [ ] Regime analysis splits (VIX / NBER / rate regime)
- [ ] CPCV (Combinatorial Purged CV)

## Phase 2.5 — Meta-learning + community 🟡 scaffolded

- [x] Meta governance files: `north_star.md` (immutable goal), `actor.md` (mutable policy), `critique.md` (mutable, learn-edited), `learn.md` (immutable meta-meta), `community.md` (mutable crowdsourcing)
- [x] Asymmetric loss function: `L = 5·FN + 1·FP + 2·|repl_score − 0.6|` (FN weighted 5× because losing real signal is permanent)
- [x] Calibration metric logger (`alpha_archive/meta/calibration.py`)
- [x] Eval loop runner (`alpha_archive/meta/eval_loop.py`)
- [x] Community layer scaffolded: 7 SQLAlchemy models, 5-gate Community-Notes-style verification, reputation system, faction-bipartisan agreement, GitHub-issue scraper (no social-media trawl)
- [ ] Critic agent that reads ReplicationReport and applies critique.md rubric
- [ ] Weekly cron: actor self-edits + learn-proposed PRs
- [ ] Public landing page per merged community contribution

## Phase 3 — Web MVP (Streamlit)

- [ ] Streamlit dashboard
  - paper list with filters (source, status, tradable, sharpe>X)
  - per-paper detail page (spec, code, IC chart, equity curve, regime breakdown)
  - search by title/author/keyword
- [ ] Public deployment on Streamlit Cloud / Render
- [ ] Basic SEO (per-paper canonical URL, OG tags, sitemap)

## Phase 4 — Public launch (alpha-archive.io)

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
- [ ] Research papers: Alpha Archive itself publishes findings on factor zoo behavior

## Non-goals (intentionally not building)

- Custom QP solver (use OSQP/CVXPY)
- Proprietary data vendor (use commodity providers + caching)
- Live execution platform (focus is research, not trading)
- Mobile app (web is sufficient)
- Crypto-only (markets too immature for replication)
