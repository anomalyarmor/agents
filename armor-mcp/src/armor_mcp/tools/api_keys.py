"""API key information tools (read-only)."""

import asyncio

from mcp.types import ToolAnnotations

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import sdk_tool

_VALID_API_KEY_VIEWS = ("list", "detail", "usage")


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
    tags={"api-keys", "read"},
)
@sdk_tool
async def get_api_key_info(
    view: str = "list",
    key_id: str | None = None,
):
    """View API key information (read-only). Cannot create or revoke keys.

    Args:
        view: What to show:
              "list" - list all API keys with names and last-used dates
              "detail" - get details of a specific key (requires key_id)
              "usage" - show API usage statistics
        key_id: API key UUID (required for view="detail")
    """
    if view not in _VALID_API_KEY_VIEWS:
        raise ValueError(
            f"Invalid view '{view}'. " f"Must be: {', '.join(_VALID_API_KEY_VIEWS)}"
        )

    client = _get_client()

    if view == "list":
        return await asyncio.to_thread(client.api_keys.list)
    elif view == "detail":
        if not key_id:
            raise ValueError("key_id is required for 'detail' view")
        return await asyncio.to_thread(client.api_keys.get, key_id)
    elif view == "usage":
        return await asyncio.to_thread(client.api_keys.usage)
    else:
        raise ValueError(
            f"Unhandled view '{view}', update dispatch to match _VALID_API_KEY_VIEWS"
        )
