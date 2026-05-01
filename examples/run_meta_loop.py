"""End-to-end demo: run the meta-learning evaluation loop.

Evaluates every fixture's reference implementation through the full backtest
pipeline. Reports per-fixture verdict + aggregate platform metrics. Logs to
data/meta_runs/metrics.jsonl for trend tracking. Alerts on regression.

Run:
    PYTHONPATH=src uv run python -m examples.run_meta_loop
"""
from __future__ import annotations

from pathlib import Path

from alphascope.meta.eval_loop import evaluate_all_fixtures
from alphascope.meta.calibration import log_metrics, platform_metrics, regression_check


def main():
    print("Running meta-learning evaluation loop on all fixtures with reference impls...")
    summary = evaluate_all_fixtures(
        start="2014-01-01",
        end="2026-04-01",
        cost_bps=5.0,
        output_path=Path("data/meta_runs/latest.json"),
    )

    print(summary.summarize())

    # Per-class F1
    print("Per-class F1 (precision / recall / F1):")
    for cls, m in summary.f1_per_class.items():
        print(f"  {cls:8s}  P={m['precision']:.2f}  R={m['recall']:.2f}  F1={m['f1']:.2f}  "
              f"(tp={m['tp']} fp={m['fp']} fn={m['fn']})")

    print("\nConfusion matrix (expected -> actual):")
    for exp, actuals in summary.confusion_matrix.items():
        for act, n in actuals.items():
            marker = "[OK]" if exp == act else "[!!]"
            print(f"  {marker} {exp:8s} -> {act:8s}: {n}")

    print("\nPer-fixture detail:")
    for r in summary.fixtures:
        marker = "[OK]" if r.verdict_match else "[FAIL]"
        print(f"\n{marker} {r.fixture_id}")
        print(f"      expected_verdict={r.expected_verdict}, actual={r.actual_verdict}")
        print(f"      expected_sharpe={r.expected_sharpe_range}, actual={r.actual_sharpe:.3f}, in_range={r.sharpe_in_range}")
        print(f"      expected_sign={r.expected_sign}, actual={r.actual_sign}, ic_mean={r.actual_ic_mean:.4f}")
        print(f"      replication_score={r.replication_score}")
        for reason in r.failure_reasons:
            print(f"      - FAIL: {reason}")

    # Regression check vs previous run
    alerts = regression_check(summary)
    if alerts:
        print("\n*** REGRESSION ALERTS ***")
        for a in alerts:
            print(f"  ! {a}")
    else:
        print("\nNo regressions vs previous run.")

    # Log + show platform trend
    log_metrics(summary)
    pm = platform_metrics(window=10)
    print(f"\nPlatform trend (last {pm.get('runs', 0)} runs):")
    for k, v in pm.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
