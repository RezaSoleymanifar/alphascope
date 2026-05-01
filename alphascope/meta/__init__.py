"""Meta-learning loop: evaluate the AlphaScope pipeline against ground-truth fixtures.
Reports precision/recall/F1; alerts on regressions; calibrates thresholds.
"""
from .eval_loop import evaluate_all_fixtures, FixtureResult, MetaSummary
from .calibration import platform_metrics

__all__ = ["evaluate_all_fixtures", "FixtureResult", "MetaSummary", "platform_metrics"]
