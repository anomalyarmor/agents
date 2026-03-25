"""Shared decorators and utilities for MCP tool functions."""

from __future__ import annotations

import asyncio
from functools import wraps
from typing import Any, Callable

from fastmcp.exceptions import ToolError


def _attr(obj: Any, key: str, default: Any = None) -> Any:
    """Get attribute from a Pydantic model or dict.

    The SDK may return either Pydantic models (with .field access) or
    raw dicts (with ["key"] access) depending on version and endpoint.
    This helper normalizes access to avoid repeated hasattr/get patterns.

    Dict check comes first to avoid returning bound methods (e.g.,
    dict.get, dict.items) when the key collides with a dict method name.
    """
    if isinstance(obj, dict):
        return obj.get(key, default)
    if hasattr(obj, key):
        return getattr(obj, key)
    return default


def _serialize(result: Any) -> Any:
    """Serialize SDK results (Pydantic models, lists, dicts) to JSON-safe dicts.

    Used by both tools (return dict) and resources (dict then json.dumps).
    """
    if isinstance(result, list):
        return [
            item.model_dump() if hasattr(item, "model_dump") else item
            for item in result
        ]
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if isinstance(result, dict):
        return result
    return {"result": result}


def sdk_tool(func: Callable) -> Callable:
    """Decorator for SDK-wrapping tools.

    Handles two cross-cutting concerns:
    1. Serialization: Pydantic models/lists -> dicts via _serialize()
    2. Error boundary: Exceptions -> FastMCP ToolError (proper MCP error channel)

    Supports both sync and async tool functions.
    """
    if asyncio.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                result = await func(*args, **kwargs)
                return _serialize(result)
            except (KeyboardInterrupt, SystemExit):
                raise
            except ToolError:
                raise
            except Exception as e:
                raise ToolError(str(e)) from e

        return async_wrapper
    else:

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                result = func(*args, **kwargs)
                return _serialize(result)
            except (KeyboardInterrupt, SystemExit):
                raise
            except ToolError:
                raise
            except Exception as e:
                raise ToolError(str(e)) from e

        return sync_wrapper
