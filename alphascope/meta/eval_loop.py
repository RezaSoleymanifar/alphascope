"""Run every fixture's reference implementation through the pipeline and
compare measured vs expected outcomes. Output: per-fixture pass/fail + aggregate
F1.
"""
from __future__ import annotations

import importlib
import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..backtest import run_signal_backtest, BacktestResult
from ..fixtures import FIXTURES, Fixture


@dataclass
class FixtureResult:
    fixture_id: str
    expected_verdict: str
    actual_verdict: str
    verdict_match: bool

    expected_sharpe_range: tuple[float, float]
    actual_sharpe: float
    sharpe_in_range: bool

    expected_ic_min: float
    actual_ic_mean: float
    ic_pass: bool

    expected_sign: str
    actual_sign: str
    sign_match: bool

    replication_score: Optional[float]

    failure_reasons: list[str] = field(default_factory=list)


@dataclass
class MetaSummary:
    timestamp: str
    n_fixtures: int
    verdict_accuracy: float       # exact match
    sharpe_in_range_rate: float
    sign_match_rate: float
    ic_pass_rate: float
    confusion_matrix: dict        # {expected_verdict: {actual_verdict: count}}
    f1_per_class: dict
    fixtures: list[FixtureResult]

    # Asymmetric loss
    n_false_negatives: int        # expected ship, got kill = LOSING REAL ALPHA
    n_false_positives: int        # expected kill, got ship = ACCEPTING NOISE
    asymmetric_loss: float        # 5 * FN + 1 * FP

    def summarize(self) -> str:
        return (
            f"\n=== MetaSummary ({self.timestamp}) ===\n"
            f"  n_fixtures: {self.n_fixtures}\n"
            f"  verdict_accuracy:      {self.verdict_accuracy*100:.1f}%\n"
            f"  sharpe_in_range_rate:  {self.sharpe_in_range_rate*100:.1f}%\n"
            f"  sign_match_rate:       {self.sign_match_rate*100:.1f}%\n"
            f"  ic_pass_rate:          {self.ic_pass_rate*100:.1f}%\n"
            f"  false_negatives:       {self.n_false_negatives} (lost real signals)\n"
            f"  false_positives:       {self.n_false_positives} (accepted noise)\n"
            f"  asymmetric_loss (5*FN+FP): {self.asymmetric_loss}\n"
        )


def _load_reference_signal(fx: Fixture):
    if not fx.reference_module:
        return None
    try:
        mod = importlib.import_module(fx.reference_module)
        return getattr(mod, "signal")
    except (ImportError, AttributeError):
        return None


def _evaluate_fixture(
    fx: Fixture,
    *,
    start: str,
    end: str,
    cost_bps: float,
) -> FixtureResult:
    sig_fn = _load_reference_signal(fx)
    if sig_fn is None:
        return FixtureResult(
            fixture_id=fx.fixture_id,
            expected_verdict=fx.expected_verdict,
            actual_verdict="error",
            verdict_match=False,
            expected_sharpe_range=fx.expected_sharpe_post_costs,
            actual_sharpe=float("nan"),
            sharpe_in_range=False,
            expected_ic_min=fx.expected_ic_min,
            actual_ic_mean=float("nan"),
            ic_pass=False,
            expected_sign=fx.expected_signal_sign,
            actual_sign="unknown",
            sign_match=False,
            replication_score=None,
            failure_reasons=["no reference implementation"],
        )

    try:
        result: BacktestResult = run_signal_backtest(
            signal_fn=sig_fn,
            signal_name=fx.fixture_id,
            universe=fx.expected_universe,
            start=start,
            end=end,
            horizon_days=fx.expected_horizon_days,
            cost_bps=cost_bps,
            n_trials_for_dsr=1,
            long_only=False,
            expected_sharpe=fx.expected_sharpe_post_costs,
            oos_split_date="2024-01-01",
        )
    except Exception as e:
        return FixtureResult(
            fixture_id=fx.fixture_id,
            expected_verdict=fx.expected_verdict,
            actual_verdict="error",
            verdict_match=False,
            expected_sharpe_range=fx.expected_sharpe_post_costs,
            actual_sharpe=float("nan"),
            sharpe_in_range=False,
            expected_ic_min=fx.expected_ic_min,
            actual_ic_mean=float("nan"),
            ic_pass=False,
            expected_sign=fx.expected_signal_sign,
            actual_sign="unknown",
            sign_match=False,
            replication_score=None,
            failure_reasons=[f"runtime error: {e}"],
        )

    actual_sharpe = result.sharpe
    lo, hi = fx.expected_sharpe_post_costs
    in_range = (lo <= actual_sharpe <= hi)
    actual_ic = result.ic_report.ic_mean
    ic_pass = (
        not math.isnan(actual_ic)
        and (
            (fx.expected_signal_sign == "+" and actual_ic >= fx.expected_ic_min)
            or (fx.expected_signal_sign == "-" and actual_ic <= -fx.expected_ic_min)
            or (fx.expected_signal_sign == "both" and abs(actual_ic) >= fx.expected_ic_min)
        )
    )
    actual_sign = "+" if actual_ic > 0 else "-" if actual_ic < 0 else "0"
    sign_match = (
        fx.expected_signal_sign == "both" or actual_sign == fx.expected_signal_sign
    )
    verdict_match = result.verdict == fx.expected_verdict

    failure_reasons = []
    if not verdict_match:
        failure_reasons.append(f"verdict {result.verdict} != expected {fx.expected_verdict}")
    if not in_range:
        failure_reasons.append(f"Sharpe {actual_sharpe:.3f} outside expected range {fx.expected_sharpe_post_costs}")
    if not ic_pass:
        failure_reasons.append(f"IC {actual_ic:.4f} fails threshold (sign {fx.expected_signal_sign}, min {fx.expected_ic_min})")
    if not sign_match:
        failure_reasons.append(f"sign {actual_sign} != expected {fx.expected_signal_sign}")

    return FixtureResult(
        fixture_id=fx.fixture_id,
        expected_verdict=fx.expected_verdict,
        actual_verdict=result.verdict,
        verdict_match=verdict_match,
        expected_sharpe_range=fx.expected_sharpe_post_costs,
        actual_sharpe=actual_sharpe,
        sharpe_in_range=in_range,
        expected_ic_min=fx.expected_ic_min,
        actual_ic_mean=actual_ic,
        ic_pass=ic_pass,
        expected_sign=fx.expected_signal_sign,
        actual_sign=actual_sign,
        sign_match=sign_match,
        replication_score=result.replication_score,
        failure_reasons=failure_reasons,
    )


def evaluate_all_fixtures(
    *,
    start: str = "2014-01-01",
    end: str = "2026-04-01",
    cost_bps: float = 5.0,
    output_path: Path | None = None,
) -> MetaSummary:
    results: list[FixtureResult] = []
    for fx in FIXTURES:
        if fx.reference_module is None:
            # skip fixtures without reference impl (pipeline must auto-generate later)
            continue
        print(f"  evaluating {fx.fixture_id}...")
        results.append(_evaluate_fixture(fx, start=start, end=end, cost_bps=cost_bps))

    n = len(results)
    if n == 0:
        raise RuntimeError("no fixtures had reference implementations")

    verdict_match_n = sum(1 for r in results if r.verdict_match)
    sharpe_in_range_n = sum(1 for r in results if r.sharpe_in_range)
    sign_match_n = sum(1 for r in results if r.sign_match)
    ic_pass_n = sum(1 for r in results if r.ic_pass)

    # Confusion matrix
    confusion = {}
    for r in results:
        confusion.setdefault(r.expected_verdict, {})
        confusion[r.expected_verdict][r.actual_verdict] = (
            confusion[r.expected_verdict].get(r.actual_verdict, 0) + 1
        )

    # F1 per class
    classes = ["ship", "iterate", "kill"]
    f1_per_class = {}
    for c in classes:
        tp = sum(1 for r in results if r.expected_verdict == c and r.actual_verdict == c)
        fp = sum(1 for r in results if r.expected_verdict != c and r.actual_verdict == c)
        fn = sum(1 for r in results if r.expected_verdict == c and r.actual_verdict != c)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        f1_per_class[c] = {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}

    n_fn = sum(
        1 for r in results
        if r.expected_verdict == "ship" and r.actual_verdict == "kill"
    )
    n_fp = sum(
        1 for r in results
        if r.expected_verdict == "kill" and r.actual_verdict == "ship"
    )

    summary = MetaSummary(
        timestamp=datetime.utcnow().isoformat(),
        n_fixtures=n,
        verdict_accuracy=verdict_match_n / n,
        sharpe_in_range_rate=sharpe_in_range_n / n,
        sign_match_rate=sign_match_n / n,
        ic_pass_rate=ic_pass_n / n,
        confusion_matrix=confusion,
        f1_per_class=f1_per_class,
        fixtures=results,
        n_false_negatives=n_fn,
        n_false_positives=n_fp,
        asymmetric_loss=5 * n_fn + 1 * n_fp,
    )

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w") as f:
            json.dump(asdict(summary), f, indent=2, default=str)

    return summary


if __name__ == "__main__":
    summary = evaluate_all_fixtures(output_path=Path("data/meta_runs/latest.json"))
    print(summary.summarize())
    print("\nPer-fixture detail:\n")
    for r in summary.fixtures:
        marker = "[OK]" if r.verdict_match else "[FAIL]"
        print(f"{marker} {r.fixture_id:35s}  expected={r.expected_verdict:8s}  got={r.actual_verdict:8s}  Sharpe={r.actual_sharpe:.3f} IC={r.actual_ic_mean:.4f}")
        for reason in r.failure_reasons:
            print(f"      - {reason}")
