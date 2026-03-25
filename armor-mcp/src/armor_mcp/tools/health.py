"""Health & discovery tools."""

import asyncio

from mcp.types import ToolAnnotations

from armor_mcp._app import mcp
from armor_mcp._client import _get_client
from armor_mcp._decorators import sdk_tool


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
    tags={"health", "read"},
)
@sdk_tool
async def health_summary():
    """Start here for a quick overview of data health.

    Returns aggregated status across alerts, freshness, schema drift,
    metrics, and validity. For per-table details, use check_freshness
    or list_schema_changes.
    """
    client = _get_client()
    return await asyncio.to_thread(client.health.summary)


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
    tags={"health", "read"},
)
@sdk_tool
async def get_todays_briefing():
    """Get today's data health briefing with key events and recommendations.

    Provides a daily summary of alerts fired, freshness issues, schema changes,
    and suggested actions. Good starting point for a morning check-in.
    """
    client = _get_client()
    return await asyncio.to_thread(client.briefings.today)
