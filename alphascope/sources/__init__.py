"""Paper source pollers. Each module exposes:
    poll() -> list[dict]   # standardized paper records
"""
from .arxiv import poll_arxiv
from .ssrn import poll_ssrn
from .nber import poll_nber
from .alpha_architect import poll_alpha_architect

__all__ = ["poll_arxiv", "poll_ssrn", "poll_nber", "poll_alpha_architect"]
