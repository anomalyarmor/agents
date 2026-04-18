"""Normalize SDK return values into plain JSON-serializable structures.

The flagship MCP tools get back Pydantic models from the Python SDK, but
the templates + ``json.dumps`` in the ``TextContent`` payload want plain
dicts. Convert once at the edge so templates don't have to care which
shape they received.
"""

from __future__ import annotations

from typing import Any


def to_plain(obj: Any) -> Any:
    """Convert Pydantic models / lists-of-models to plain dicts.

    Idempotent: dicts and primitives pass through untouched.
    """
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, list):
        return [to_plain(item) for item in obj]
    if isinstance(obj, tuple):
        return [to_plain(item) for item in obj]
    if isinstance(obj, dict):
        return {key: to_plain(value) for key, value in obj.items()}
    return obj
