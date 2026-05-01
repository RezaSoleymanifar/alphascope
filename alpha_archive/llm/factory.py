"""Provider selection. Reads ALPHA_ARCHIVE_LLM_PROVIDER env var.

Order of fallback:
  1. explicit override (function arg or env var)
  2. anthropic if ANTHROPIC_API_KEY set
  3. claude_code if `claude` CLI on PATH
  4. offline (always available)
"""
from __future__ import annotations

import os
import shutil
from functools import cache
from typing import Optional

from .base import LLMProvider


def _build(name: str) -> LLMProvider:
    n = name.lower().strip()
    if n in ("anthropic", "api"):
        from .anthropic_provider import AnthropicProvider
        return AnthropicProvider()
    if n in ("claude_code", "cli", "code"):
        from .claude_code_provider import ClaudeCodeProvider
        return ClaudeCodeProvider()
    if n in ("offline", "stub", "none"):
        from .offline_provider import OfflineProvider
        return OfflineProvider()
    raise ValueError(f"unknown LLM provider: {name}")


@cache
def get_provider(override: Optional[str] = None) -> LLMProvider:
    """Pick provider. Cached: same provider returned on subsequent calls."""
    chosen = override or os.environ.get("ALPHA_ARCHIVE_LLM_PROVIDER")
    if chosen:
        return _build(chosen)

    # auto-detect order
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return _build("anthropic")
        except Exception:
            pass
    if shutil.which("claude"):
        return _build("claude_code")
    return _build("offline")


def info() -> dict:
    """Diagnostic: which provider would be used and why."""
    p = get_provider()
    return {
        "selected": p.name,
        "anthropic_key_present": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "claude_cli_on_path": shutil.which("claude") is not None,
        "override": os.environ.get("ALPHA_ARCHIVE_LLM_PROVIDER"),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(info(), indent=2))
