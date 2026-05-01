"""SQLite schema + ORM models for AlphaScope.

Three core tables:
- papers: ingested papers from any source (arXiv, SSRN, NBER, manual)
- specs: LLM-extracted signal specifications per paper
- results: backtest results per (paper, spec, run)
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "alphascope.sqlite"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

ENGINE = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
Session = sessionmaker(bind=ENGINE, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Paper(Base):
    __tablename__ = "papers"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_source_eid"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(32), index=True)  # arxiv, ssrn, nber, manual
    external_id: Mapped[str] = mapped_column(String(256), index=True)
    title: Mapped[str] = mapped_column(Text)
    abstract: Mapped[Optional[str]] = mapped_column(Text)
    authors: Mapped[Optional[str]] = mapped_column(Text)  # comma-separated
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    pdf_url: Mapped[Optional[str]] = mapped_column(Text)
    landing_url: Mapped[Optional[str]] = mapped_column(Text)
    categories: Mapped[Optional[str]] = mapped_column(String(256))
    raw: Mapped[Optional[dict]] = mapped_column(JSON)

    # workflow status
    triage_status: Mapped[str] = mapped_column(String(16), default="pending")
    # pending | tradable | not_tradable | error

    triage_score: Mapped[Optional[float]] = mapped_column(Float)
    triage_notes: Mapped[Optional[str]] = mapped_column(Text)
    triaged_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    extracted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    inserted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    specs = relationship("Spec", back_populates="paper", cascade="all, delete-orphan")


class Spec(Base):
    __tablename__ = "specs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("papers.id"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    # LLM-extracted signal definition
    hypothesis: Mapped[Optional[str]] = mapped_column(Text)
    formula: Mapped[Optional[str]] = mapped_column(Text)
    data_required: Mapped[Optional[dict]] = mapped_column(JSON)  # {prices: y, fundamentals: [pe], macro: [vix]}
    universe: Mapped[Optional[str]] = mapped_column(String(64))  # sp500, russell1000, etc.
    rebalance_freq: Mapped[Optional[str]] = mapped_column(String(16))  # daily, weekly, monthly
    horizon_days: Mapped[Optional[int]] = mapped_column(Integer)
    expected_sign: Mapped[Optional[str]] = mapped_column(String(8))  # +, -, both
    claimed_sharpe: Mapped[Optional[float]] = mapped_column(Float)
    claimed_period: Mapped[Optional[str]] = mapped_column(String(64))
    code: Mapped[Optional[str]] = mapped_column(Text)  # generated Python feature implementation

    inserted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    paper = relationship("Paper", back_populates="specs")
    results = relationship("Result", back_populates="spec", cascade="all, delete-orphan")


class Result(Base):
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    spec_id: Mapped[int] = mapped_column(ForeignKey("specs.id"), index=True)
    run_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # input data window
    train_start: Mapped[Optional[str]] = mapped_column(String(16))
    train_end: Mapped[Optional[str]] = mapped_column(String(16))
    oos_start: Mapped[Optional[str]] = mapped_column(String(16))
    oos_end: Mapped[Optional[str]] = mapped_column(String(16))

    # IC report
    ic_mean: Mapped[Optional[float]] = mapped_column(Float)
    ic_std: Mapped[Optional[float]] = mapped_column(Float)
    icir: Mapped[Optional[float]] = mapped_column(Float)
    ic_t_stat: Mapped[Optional[float]] = mapped_column(Float)
    ic_p_value: Mapped[Optional[float]] = mapped_column(Float)

    # Strategy stats
    sharpe: Mapped[Optional[float]] = mapped_column(Float)
    sharpe_oos: Mapped[Optional[float]] = mapped_column(Float)
    deflated_sharpe: Mapped[Optional[float]] = mapped_column(Float)
    ann_return: Mapped[Optional[float]] = mapped_column(Float)
    ann_vol: Mapped[Optional[float]] = mapped_column(Float)
    max_drawdown: Mapped[Optional[float]] = mapped_column(Float)
    calmar: Mapped[Optional[float]] = mapped_column(Float)
    turnover: Mapped[Optional[float]] = mapped_column(Float)

    # Replication score: claimed_sharpe vs measured_sharpe
    replication_score: Mapped[Optional[float]] = mapped_column(Float)

    verdict: Mapped[Optional[str]] = mapped_column(String(16))  # ship | iterate | kill
    notes: Mapped[Optional[str]] = mapped_column(Text)
    artifacts: Mapped[Optional[dict]] = mapped_column(JSON)  # paths to plots, parquet, etc.

    spec = relationship("Spec", back_populates="results")


def init_db():
    """Create all tables. Idempotent."""
    Base.metadata.create_all(ENGINE)
    return DB_PATH


if __name__ == "__main__":
    p = init_db()
    print(f"initialized SQLite at {p}")
