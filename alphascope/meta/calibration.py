"""Platform-wide metrics tracked over time. Detects drift and informs threshold tuning."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .eval_loop import MetaSummary

METRICS_LOG = Path("data/meta_runs/metrics.jsonl")


def log_metrics(summary: MetaSummary):
    """Append summary to JSONL log for time-series tracking."""
    METRICS_LOG.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": summary.timestamp,
        "n_fixtures": summary.n_fixtures,
        "verdict_accuracy": summary.verdict_accuracy,
        "sharpe_in_range_rate": summary.sharpe_in_range_rate,
        "sign_match_rate": summary.sign_match_rate,
        "ic_pass_rate": summary.ic_pass_rate,
        "n_false_negatives": summary.n_false_negatives,
        "n_false_positives": summary.n_false_positives,
        "asymmetric_loss": summary.asymmetric_loss,
        "f1_ship": summary.f1_per_class.get("ship", {}).get("f1"),
        "f1_iterate": summary.f1_per_class.get("iterate", {}).get("f1"),
        "f1_kill": summary.f1_per_class.get("kill", {}).get("f1"),
    }
    with METRICS_LOG.open("a") as f:
        f.write(json.dumps(record) + "\n")


def platform_metrics(window: int = 10) -> dict:
    """Return aggregated platform metrics over last `window` runs."""
    if not METRICS_LOG.exists():
        return {"runs": 0, "note": "no history yet"}
    rows = []
    with METRICS_LOG.open() as f:
        for line in f:
            rows.append(json.loads(line))
    rows = rows[-window:]
    if not rows:
        return {"runs": 0}
    n = len(rows)
    return {
        "runs": n,
        "mean_verdict_accuracy": sum(r["verdict_accuracy"] for r in rows) / n,
        "mean_sharpe_in_range_rate": sum(r["sharpe_in_range_rate"] for r in rows) / n,
        "mean_asymmetric_loss": sum(r["asymmetric_loss"] for r in rows) / n,
        "trend_asymmetric_loss": rows[-1]["asymmetric_loss"] - rows[0]["asymmetric_loss"],
        "latest_run": rows[-1]["timestamp"],
    }


def regression_check(current: MetaSummary) -> list[str]:
    """Compare current run to last logged run; return list of regression alerts."""
    if not METRICS_LOG.exists():
        return []
    prev_rows = []
    with METRICS_LOG.open() as f:
        for line in f:
            prev_rows.append(json.loads(line))
    if not prev_rows:
        return []
    prev = prev_rows[-1]

    alerts = []
    if current.verdict_accuracy < prev["verdict_accuracy"] - 0.05:
        alerts.append(
            f"verdict_accuracy dropped {prev['verdict_accuracy']:.2%} -> {current.verdict_accuracy:.2%}"
        )
    if current.n_false_negatives > prev.get("n_false_negatives", 0):
        alerts.append(
            f"false_negatives rose {prev.get('n_false_negatives', 0)} -> {current.n_false_negatives} (LOSING ALPHA)"
        )
    if current.asymmetric_loss > prev["asymmetric_loss"] * 1.2:
        alerts.append(
            f"asymmetric_loss jumped {prev['asymmetric_loss']} -> {current.asymmetric_loss}"
        )
    return alerts
