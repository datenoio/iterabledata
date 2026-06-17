"""Uniform tool result helpers for agent integrations."""

from __future__ import annotations

from typing import Any


def tool_success(data: Any) -> dict[str, Any]:
    """Return a successful tool result envelope."""
    return {"ok": True, "data": data}


def tool_error(message: str, *, code: str | None = None, details: Any = None) -> dict[str, Any]:
    """Return a failed tool result envelope."""
    result: dict[str, Any] = {"ok": False, "error": message}
    if code is not None:
        result["code"] = code
    if details is not None:
        result["details"] = details
    return result
