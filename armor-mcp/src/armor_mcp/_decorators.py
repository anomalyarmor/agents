"""Shared decorators and utilities for MCP tool functions."""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class ToolError(Exception):
    """Structured error for tool functions.

    Allows tools to return error responses with extra context fields
    (e.g., oauth_url) through the sdk_tool error boundary, while
    keeping a consistent {"error": ..., "message": ...} shape.

    Usage:
        raise ToolError(
            "Connect your Slack workspace first.",
            error_type="NoSlackConnection",
            oauth_url="https://...",
        )
        # sdk_tool serializes to:
        # {"error": "NoSlackConnection", "message": "Connect your...", "oauth_url": "https://..."}
    """

    def __init__(self, message: str, error_type: str = "ToolError", **details: Any):
        super().__init__(message)
        self.error_type = error_type
        self.details = details


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


def sdk_tool(func: Callable[..., T]) -> Callable[..., dict | list[dict]]:
    """Decorator for SDK-wrapping tools.

    Handles:
    - Pydantic model serialization via model_dump()
    - ToolError with structured details (extra fields preserved)
    - Generic exception handling with typed error responses
    - List serialization
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> dict | list[dict]:
        try:
            result = func(*args, **kwargs)
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
        except (KeyboardInterrupt, SystemExit):
            raise
        except ToolError as e:
            response: dict[str, Any] = {"error": e.error_type, "message": str(e)}
            response.update(e.details)
            return response
        except Exception as e:
            return {"error": type(e).__name__, "message": str(e)}

    return wrapper
