"""Pluggable LLM provider abstraction.

Multiple backends:
- claude_code:  shells out to `claude -p` (free if you have a Max plan via CLI)
- anthropic:    uses anthropic SDK with API key
- offline:      regex/template fallback (no LLM, for testing plumbing)

Switch via env var ALPHA_ARCHIVE_LLM_PROVIDER; defaults to claude_code.
"""
from .base import LLMProvider, LLMResponse
from .factory import get_provider

__all__ = ["LLMProvider", "LLMResponse", "get_provider"]
