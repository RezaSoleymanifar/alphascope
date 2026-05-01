"""LLM-driven paper extraction pipeline.
PDF -> text -> structured spec -> Python code -> sandbox-validated -> backtest-ready.
"""
from .pdf import download_pdf, extract_text
from .spec import extract_spec, SignalSpec
from .codegen import generate_signal_code, validate_code
from .sandbox import run_in_sandbox

__all__ = [
    "download_pdf", "extract_text",
    "extract_spec", "SignalSpec",
    "generate_signal_code", "validate_code",
    "run_in_sandbox",
]
