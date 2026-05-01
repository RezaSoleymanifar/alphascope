"""AlphaScope CLI."""
from __future__ import annotations

import json

import typer
from rich import print as rprint
from rich.table import Table

from .db import init_db, Paper, Session
from .ingest import ingest as ingest_fn, SOURCES
from .triage import triage_pending
from sqlalchemy import select, func

app = typer.Typer(help="AlphaScope — paper-to-backtest replication engine")


@app.command("init")
def cmd_init():
    """Initialize SQLite database."""
    p = init_db()
    rprint(f"[green]initialized[/green] {p}")


@app.command("poll")
def cmd_poll(
    source: str = typer.Argument("all", help=f"one of {list(SOURCES.keys())} or 'all'"),
    limit: int = typer.Option(None, help="max papers per source"),
):
    """Poll source(s) for new papers."""
    summary = ingest_fn(source=source, limit=limit)
    table = Table(title=f"ingest summary ({source})")
    table.add_column("source")
    table.add_column("new", justify="right")
    table.add_column("dup", justify="right")
    table.add_column("polled", justify="right")
    for src, stats in summary.items():
        table.add_row(src, str(stats["new"]), str(stats["duplicate"]), str(stats["total_polled"]))
    rprint(table)


@app.command("triage")
def cmd_triage(
    limit: int = typer.Option(50, help="max papers to triage"),
    dry_run: bool = typer.Option(False, help="don't call LLM, just list"),
):
    """LLM-triage pending papers."""
    summary = triage_pending(limit=limit, dry_run=dry_run)
    rprint(json.dumps(summary, indent=2))


@app.command("stats")
def cmd_stats():
    """Show per-source paper counts and triage status."""
    init_db()
    with Session() as s:
        rows = s.execute(
            select(Paper.source, Paper.triage_status, func.count())
            .group_by(Paper.source, Paper.triage_status)
        ).all()
    table = Table(title="paper counts")
    table.add_column("source")
    table.add_column("triage_status")
    table.add_column("count", justify="right")
    for src, status, n in sorted(rows):
        table.add_row(src or "?", status or "?", str(n))
    rprint(table)


@app.command("list")
def cmd_list(
    source: str = typer.Option(None),
    status: str = typer.Option(None, help="pending|tradable|not_tradable|error"),
    limit: int = typer.Option(20),
):
    """List papers (filterable)."""
    init_db()
    with Session() as s:
        q = select(Paper).order_by(Paper.published_at.desc().nulls_last()).limit(limit)
        if source:
            q = q.where(Paper.source == source)
        if status:
            q = q.where(Paper.triage_status == status)
        rows = list(s.scalars(q))
    table = Table(title=f"papers (limit {limit})")
    table.add_column("id", justify="right")
    table.add_column("source")
    table.add_column("status")
    table.add_column("published")
    table.add_column("title")
    for p in rows:
        table.add_row(
            str(p.id),
            p.source,
            p.triage_status,
            (p.published_at.isoformat()[:10] if p.published_at else ""),
            (p.title or "")[:80],
        )
    rprint(table)


if __name__ == "__main__":
    app()
